import json
import os
import re
import yaml
from openai import OpenAI
from pinecone import Pinecone
from dotenv import load_dotenv
from pydantic import BaseModel
from typing import Optional, List
import sqlite3

class QueryResponse(BaseModel):
    need_retrieve: bool
    need_filtering_expression: bool
    filtering_expression: Optional[str] = None
    vector_search_criteria: str


class CheeseRetriever:
    def __init__(self, config_path='config/config.yaml', db_path='data/cheese.db'):
        # Load configuration
        with open(config_path, 'r') as file:
            self.config = yaml.safe_load(file)
        
        # Load environment variables
        load_dotenv()
        
        # Initialize OpenAI client
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
        # Initialize Pinecone for vector search only
        self.pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
        self.index = self.pc.Index(self.config['vector_db']['pinecone']['index_name'])
        
        # Initialize SQLite connection
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.cursor = self.conn.cursor()
    
    def retrieve(self, user_question, top_k=5):
        """Retrieve cheese information using vector search + SQLite filtering."""
        # Generate embedding for semantic search
        embedding = self.generate_embedding(user_question)
        
        # Generate SQL query from user question
        sql_query, use_sql_filtering, is_cheese_question = self.generate_sql_query(user_question)
        
        # If not a cheese question, return empty results
        if not is_cheese_question:
            return []
        
        if use_sql_filtering:
            # Approach 1: SQL first, then vector search on filtered IDs
            cheese_upc = self.execute_sql_query(sql_query)
            print(cheese_upc)
            # If no results from SQL, fall back to vector-only search
            if not cheese_upc:
                return self.vector_only_search(embedding, top_k)
            
            # Do vector search with ID filter
            results = self.index.query(
                vector=embedding,
                top_k=top_k,
                include_metadata=True,
                filter={"upc": {"$in": cheese_upc}}
            )
            # print(len(results.matches))
        else:
            # No filtering needed, do vector-only search
            return self.vector_only_search(embedding, top_k)
        
        # Process and return the results
        documents = []
        for match in results.matches:
            documents.append({
                "text": match.metadata.get("text", ""),
                "metadata": match.metadata,
                "score": match.score
            })
        
        return documents
    
    def vector_only_search(self, embedding, top_k):
        """Perform vector search without filtering"""
        results = self.index.query(
            vector=embedding,
            top_k=top_k,
            include_metadata=True
        )
        
        documents = []
        for match in results.matches:
            documents.append({
                "text": match.metadata.get("text", ""),
                "metadata": match.metadata,
                "score": match.score
            })
        
        return documents
    
    def generate_embedding(self, text):
        """Generate embedding for vector search"""
        response = self.client.embeddings.create(
            model=self.config['vector_db']['embeddings']['model'],
            input=text
        )
        return response.data[0].embedding
    
    def generate_sql_query(self, user_question):
        """Generate SQL query from user question using GPT or identify non-cheese questions."""
        system_prompt = """
        You are an AI that converts natural language questions about cheese into SQL queries.
        
        IMPORTANT: First determine if the question is actually about cheese. Questions about cheese include:
        - Inquiries about specific cheese types, brands, flavors, or properties
        - Questions about cheese pricing, origin, texture, color, etc.
        - Requests for cheese recommendations, pairings, or culinary uses
        
        If the question is NOT about cheese (like technology, politics, general knowledge, other foods, etc.),
        you MUST set "use_sql_filtering" to false and "sql_query" to empty string.
        
        The database has a table called 'cheese' with these columns:
        - id: unique identifier
        - title: cheese name
        - description: detailed cheese description
        - brand: manufacturer
        - origin: country of origin
        - color: cheese color
        - texture: texture description
        - price_per_unit: price in dollars
        - case_price: price for a case
        - each_price: price for each
        - each_weight: weight of each
        - case_weight: weight of case
        - milk_type: type of milk used (cow, goat, sheep, etc.)
        - flavor_profile: taste characteristics
        - sku: stock keeping unit
        - upc: universal product code
        - image_urls: URLs to product images (stored as JSON string)
        - url: product webpage URL
        - related_items: similar products (stored as JSON string)
        - use_cases: recommended applications (stored as JSON string)
        - vector_id: ID for vector search
        - keywords: relevant keywords (stored as JSON string)
        
        Rules:
        1. Generate a SQL query based on the user's question filtering criteria ONLY if cheese-related
        2. Return both the SQL query and a boolean indicating if filtering should be used
        3. Use LIKE with % wildcards for string searches (e.g., '%Italy%')
        4. Use appropriate numeric comparisons for prices and weights
        5. For JSON fields, use json_extract or string matching
        6. If the question is not about cheese at all, return empty query and false
        
        Output format:
        {
            "sql_query": "SELECT upc FROM cheese WHERE...",
            "use_sql_filtering": true/false,
            "is_cheese_question": true/false
        }
        
        Examples:
        Q: "Show me Italian cheeses"
        A: {
            "sql_query": "SELECT upc FROM cheese WHERE origin LIKE '%Italy%'", 
            "use_sql_filtering": true,
            "is_cheese_question": true
        }
        
        Q: "What is Python programming?"
        A: {
            "sql_query": "",
            "use_sql_filtering": false,
            "is_cheese_question": false
        }
        
        Q: "What are some cheeses good for pizza?"
        A: {
            "sql_query": "SELECT upc FROM cheese WHERE use_cases LIKE '%pizza%' OR keywords LIKE '%pizza%'",
            "use_sql_filtering": true,
            "is_cheese_question": true
        }
        """
        
        response = self.client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_question}
            ],
            response_format={"type": "json_object"}
        )
        
        result = json.loads(response.choices[0].message.content)
        is_cheese_question = result.get("is_cheese_question", False)
        
        # Return the SQL query and whether to use it, plus whether it's a cheese question
        return result["sql_query"], result["use_sql_filtering"], is_cheese_question
    
    def execute_sql_query(self, query):
        """Execute SQL query and return cheese IDs"""
        try:
            self.cursor.execute(query)
            results = self.cursor.fetchall()
            return [row[0] for row in results]  # Assuming first column is ID
        except sqlite3.Error as e:
            print(f"SQLite error: {e}")
            return []

    def generate_query_response(self, user_question):
        system_prompt = """
        You are an AI assistant that analyzes user questions to determine:
        1. If the question is related to cheese products
        2. If metadata filtering is needed and what filter to apply
        3. What vector search criteria will yield the best results

        Output object with the following structure:
        {
            "need_retrieve": true/false,   # Set true if query is about cheese, false otherwise
            "need_filtering_expression": true/false,   # Set true if metadata filtering is possible
            "filtering_expression": "filtering_expression_string_or_null",   # Valid Pinecone filter or null
            "vector_search_criteria": "optimized_search_query"   # Enhanced search query
        }

        RULES FOR DETERMINING need_retrieve:
        - Set TRUE if the query is asking about cheese products, brands, types, uses, etc.
        - Set FALSE if the query is a general question, unrelated to cheese, or a greeting

        RULES FOR DETERMINING need_filtering_expression:
        - Set TRUE if the query contains specific criteria that can be filtered using metadata only about the price and color,origin,sku,texture,brand
        - Set FALSE if the query is general, vague, or can't be filtered with available metadata fields

        VALID PINECONE FILTER OPERATORS:
        - Exact match: {"field": "value"}
        - Comparison (numeric): {"field": {"$gt": number}}, {"field": {"$gte": number}}, {"field": {"$lt": number}}, {"field": {"$lte": number}}
        - Not equal: {"field": {"$ne": "value"}}
        - In list: {"field": {"$in": ["value1", "value2"]}}
        - Not in list: {"field": {"$nin": ["value1", "value2"]}}
        - Logical AND: {"$and": [filter1, filter2, ...]}
        - Logical OR: {"$or": [filter1, filter2, ...]}

        The complete metadata schema includes:
        - all_categories, category, subcategory: Cheese categories and classifications
        - brand: Manufacturer or producer brand name
        - case_dimensions, each_dimensions: Physical dimensions information
        - case_pack_size, each_pack_size: Packaging quantity information
        - case_price, each_price, price_per_unit: Price information at different levels
        - case_weight, each_weight: Weight information at different levels
        - color: Visual color of the cheese
        - flavor_profile: Taste characteristics and flavor notes
        - image_description: Detailed description of the product
        - image_urls: URLs to product images
        - keywords: Key terms associated with the product
        - milk_type: Type of milk used (cow, goat, sheep, etc.)
        - origin: Country or region of origin
        - others_you_may_like_urls: URLs to similar products
        - related_items: Associated products (stored as a string representation of a list)
        - sku, upc: Product identification codes
        - texture: Physical texture of the cheese
        - title: Product title/name
        - url: Product URL
        - use_cases: Recommended applications and uses for the cheese
        The fields that are available in the metadata:
        - price_per_unit
        - case_price
        - each_price
        - case_weight
        - each_weight
        - color
        - origin
        - texture
        - brand
        So many filters can decrease the performance of the retrieval, so only use the fields that are available in the metadata and if you can't find the fields that are available in the metadata and so certain criteria,  then don't use any filters
        And about the price, if the word "case" or "each" or "unit" or "lb" don't appear, just use the price_per_unit.
        RULES FOR CONSTRUCTING filtering_expression:
        1. For partial text matching, Pinecone does not support substring matching
        2. For negating an exact match, use: {"field": {"$ne": "value"}}
        3. For negating multiple values, use: {"field": {"$nin": ["value1", "value2"]}}
        4. For complex conditions, use AND/OR operators: {"$and": [{"field1": "value"}, {"$or": [{...}, {...}]}]}
        5. Always use double quotes for keys and string values in the JSON


        EXAMPLES OF filtering_expression:
        - Find exact product: {"sku": "103601"}
        - Price range: {"$and": [{"price_per_unit": {"$gte": 5}}, {"price_per_unit": {"$lte": 10}}]}
        - Multiple conditions: {"$and": [{"brand": "Galbani"}, {"subcategory": "Specialty Cheese"}]}
        - Exclude American cheese: {"title": {"$ne": "American"}}
        - Find certain textures: {"texture": {"$in": ["firm", "hard"]}}
        - Exclude certain origins: {"origin": {"$nin": ["France", "Italy"]}}

        RULES FOR VECTOR SEARCH CRITERIA:
        - Rephrase vague queries to be more specific
        - Include important cheese characteristics and terms
        - For queries needing substring matching (which Pinecone can't filter), optimize vector search terms
        - Keep relevant context but make it concise and focused

        EXAMPLES:
        
        EXAMPLE 1:
        User query: "What cheeses are made in Italy?"
        Response:
        {
            "need_retrieve": true,
            "need_filtering_expression": true,
            "filtering_expression": {"origin": "Italy"},
            "vector_search_criteria": "Italian cheese varieties origin Italy"
        }
        
        EXAMPLE 2:
        User query: "What's the weather like today?"
        Response:
        {
            "need_retrieve": false,
            "need_filtering_expression": false,
            "filtering_expression": null,
            "vector_search_criteria": ""
        }
        
        EXAMPLE 3:
        User query: "I want soft creamy cheeses that work well on crackers"
        Response:
        {
            "need_retrieve": true,
            "need_filtering_expression": true,
            "filtering_expression": {"texture": "soft"},
            "vector_search_criteria": "soft creamy cheese crackers appetizer spread"
        }
        
        EXAMPLE 4:
        User query: "Do you have any cheeses with herbs?"
        Response:
        {
            "need_retrieve": true,
            "need_filtering_expression": false,
            "filtering_expression": null,
            "vector_search_criteria": "cheese with herbs flavored herbed specialty cheese"
        }
        """
        
        # Send the request to GPT
        response = self.client.beta.chat.completions.parse(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_question}
            ],
            response_format=QueryResponse,
        )
        query_response = response.choices[0].message.parsed
        return query_response

# cheese_retriever = CheeseRetriever()
# print(cheese_retriever.generate_query_response("I want to buy a cheese that related to the brand 'Galbani'"))

# Example usage
# retriever = CheeseRetriever()
# results = retriever.retrieve("I want to buy a cheese from Galbani brand")

# # Print the results
# for i, result in enumerate(results, 1):
#     print(f"Result {i} (Score: {result['score']:.4f}):")
#     print(f"Text: {result['text'][:200]}...")  # Print first 200 chars
#     print("-" * 80)