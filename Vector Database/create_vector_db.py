import os
import json
from openai import OpenAI
from pinecone import Pinecone, ServerlessSpec
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# 1. Load your data
with open('cheese_data_with_image_descriptions.json', 'r') as f:
    cheese_data = json.load(f)

# 2. Initialize OpenAI client for creating embeddings
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# 3. Initialize Pinecone client
pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))

# 4. Create a new index if it doesn't exist
index_name = "cheese-embeddings"

# Check if index exists
if index_name not in pc.list_indexes().names():
    # Create the index
    pc.create_index(
        name=index_name,
        dimension=1536,  # OpenAI embeddings dimension for text-embedding-3-small
        metric="cosine",
        spec=ServerlessSpec(cloud="aws", region="us-west-2")
    )

# Get the index
index = pc.Index(index_name)

# 5. Create embeddings and upsert to Pinecone
batch_size = 100  # Process in batches to avoid memory issues
for i in range(0, len(cheese_data), batch_size):
    batch = cheese_data[i:i+batch_size]
    
    texts = []
    ids = []
    metadata = []
    
    for idx, cheese in enumerate(batch):
        # Create a comprehensive text representation including all relevant fields
        text_parts = []
        
        if cheese.get('title'):
            text_parts.append(f"Title: {cheese.get('title', '')}")
        
        if cheese.get('brand'):
            text_parts.append(f"Brand: {cheese.get('brand', '')}")
            
        if cheese.get('sku'):
            text_parts.append(f"SKU: {cheese.get('sku', '')}")
        
        if cheese.get('upc'):
            text_parts.append(f"UPC: {cheese.get('upc', '')}")
        
        if cheese.get('each_price'):
            text_parts.append(f"Each Price: {cheese.get('each_price', '')}")
        
        if cheese.get('case_price'):
            text_parts.append(f"Case Price: {cheese.get('case_price', '')}")
        if cheese.get('each_weight'):
            text_parts.append(f"Each Weight: {cheese.get('each_weight', '')}")
        if cheese.get('case_weight'):
            text_parts.append(f"Case Weight: {cheese.get('case_weight', '')}")
        if cheese.get('each_pack_size'):
            text_parts.append(f"Each Pack Size: {cheese.get('each_pack_size', '')}")
        if cheese.get('case_pack_size'):
            text_parts.append(f"Case Pack Size: {cheese.get('case_pack_size', '')}")
        if cheese.get('each_dimensions'):
            text_parts.append(f"Each Dimensions: {cheese.get('each_dimensions', '')}")
        if cheese.get('case_dimensions'):
            text_parts.append(f"Case Dimensions: {cheese.get('case_dimensions', '')}")
            
        if 'category' in cheese and cheese['category']:
            categories = ', '.join(cheese['category']) if isinstance(cheese['category'], list) else cheese['category']
            text_parts.append(f"Category: {categories}")
        
        if cheese.get('image_description'):
            text_parts.append(f"Image Description: {cheese.get('image_description', '')}")
            
        # Join all parts with periods
        text = ". ".join(text_parts)
        
        texts.append(text)
        ids.append(f"cheese_{i+idx}")
        
        # Include relevant metadata for search filtering
        metadata_item = {
            "title": cheese.get("title", ""),
            "brand": cheese.get("brand", ""),
            "price": cheese.get("each_price", "") or cheese.get("case_price", ""),
            "url": cheese.get("url", ""),
        }
        
        # Add categories to metadata if they exist
        if 'category' in cheese and cheese['category']:
            if isinstance(cheese['category'], list):
                metadata_item["category"] = cheese['category'][0] if cheese['category'] else ""
                if len(cheese['category']) > 1:
                    metadata_item["subcategory"] = cheese['category'][1]
            else:
                metadata_item["category"] = cheese['category']
        
        metadata.append(metadata_item)
    
    # Get embeddings from OpenAI
    response = client.embeddings.create(
        input=texts,
        model="text-embedding-3-small"
    )
    
    embeddings = [item.embedding for item in response.data]
    
    # Prepare vectors for upsert
    vectors = []
    for j in range(len(embeddings)):
        vectors.append({
            "id": ids[j],
            "values": embeddings[j],
            "metadata": metadata[j]
        })
    
    # Upsert to Pinecone
    index.upsert(vectors=vectors)
    print(f"Processed and uploaded batch {i//batch_size + 1}/{(len(cheese_data) + batch_size - 1)//batch_size}")

print("Vector database created successfully!")

# Example query function
def search_cheeses(query, top_k=5):
    # Create query embedding
    query_response = client.embeddings.create(
        input=[query],
        model="text-embedding-3-small"
    )
    query_embedding = query_response.data[0].embedding
    
    # Search Pinecone
    search_results = index.query(
        vector=query_embedding,
        top_k=top_k,
        include_metadata=True
    )
    
    # Return results
    return search_results['matches']

# Example: search_results = search_cheeses("soft Italian cheese with mild flavor")
