import json
import yaml
import os
from openai import OpenAI
from datetime import datetime
import json
import os
from datetime import datetime
from .retriever import CheeseRetriever

class LLM:
    def __init__(self, config_path='config/config.yaml'):
        # Load configuration
        with open(config_path, 'r') as file:
            self.config = yaml.safe_load(file)
        
        # Initialize retriever
        self.retriever = CheeseRetriever(config_path)
        
        # Initialize OpenAI client
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
        # Initialize chat history
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.history = []
    
    def answer_question(self, user_question):
        """Generate an answer to a user's question about cheese using RAG."""
        # Add user message to history
        self.history.append({"role": "user", "content": user_question, "timestamp": datetime.now().isoformat()})
        
        # Retrieve relevant documents
        documents = self.retriever.retrieve(user_question, top_k=5)
        
        # Check if any documents were retrieved
        if not documents:
            answer = self._generate_no_info_response(user_question)
        else:
            # Format retrieved documents as context
            print(documents)
            context = json.dumps(documents)
            
            # Create prompt with context
            system_prompt = f"""
            You are an expert cheese sommelier and product specialist. Answer the user's question using the provided cheese information in comprehensive detail, including product details and shopping information.
            
            CHEESE INFORMATION:
            {context}
            
            In your response, include:
            First Show all the products in the context
            IMPORTANT INSTRUCTIONS:
            1. If the user ask more than 5(like all) products, please answer the number of products in the context. So, as default, show around suitable 5 cheese products in your response and ask "Do you want to see more?". 
            2. PRODUCT INFORMATION:
               - Product name and brand
               - URL where the product can be purchased (format as clickable link)
               - SKU/UPC codes for reference
               - Include image URLs in your response (format as markdown: ![Cheese Image](image_url))
               - Price information, weights, and packaging options
               - price per each and price per case
            
            3. CHEESE CHARACTERISTICS:
               - FLAVOR PROFILE: Describe the complex flavors, aromas, taste progression, and intensity
               - TEXTURE: Detail the mouthfeel, consistency, and physical characteristics  
               - APPEARANCE: Describe the color, rind, interior, and visual aspects
               - ORIGIN: Explain the geographical and cultural significance of this cheese
            
            4. USAGE RECOMMENDATIONS:
               - CULINARY APPLICATIONS: Provide specific recipes and preparation methods
               - PAIRINGS: Suggest complementary foods, wines, beers, or other beverages
               - SERVING RECOMMENDATIONS: Discuss ideal temperature, cutting methods, presentation
               - STORAGE: Explain proper storage conditions and shelf life
            
            5. ADDITIONAL SHOPPING HELP:
               - RELATED PRODUCTS: Mention the related items from the context
               - SIMILAR RECOMMENDATIONS: List other products the customer might enjoy
               - PRICING CONSIDERATIONS: Discuss value and what affects quality/price
            
            Guidelines:
            • Format your response in a clean, organized way with clear sections and markdown formatting
            • Include ALL available product details (URLs, SKUs, images, pricing)
            • If showing multiple products, create a separate section for each with its own details
            • For images, include at least one image URL formatted as markdown if available
            • Include links to the product and related/similar products formatted as markdown
            • Be thorough but conversational, like an enthusiastic cheese expert sharing their passion
            • Show all the products in the context
            """
            
            # Generate response
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_question}
                ],
                temperature=0.7
            )
            
            answer = response.choices[0].message.content
        
        # Add assistant response to history
        self.history.append({"role": "assistant", "content": answer, "timestamp": datetime.now().isoformat()})
        
        # Save history
        self._save_history()
        
        return answer
    

    def _generate_no_info_response(self, user_question):
        """Generate a detailed response when no specific information is available."""
        system_prompt = """
        You are a helpful, creative, and knowledgeable Cheese Expert assistant. You can answer questions on a wide range of topics
        beyond cheese. Provide accurate, informative, and thoughtful responses to the user's questions. Exactly you have detailed information about 98 cheese products.
        Politely decline to answer the question, explaining that you are specialized in cheese information only.
        
        - Be firm but friendly in your refusal
        - Do NOT provide any information on the non-cheese topic
        - Suggest they ask you about cheese instead
        - Provide a brief example of what types of cheese questions you can answer
        - Keep your response concise and clear
        
        Example refusal: "I'm sorry, but I'm a specialized cheese expert and can't answer questions about [topic].
        """
        
        response = self.client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_question}
            ],
            temperature=0.7
        )
        
        return response.choices[0].message.content

    def get_history(self):
        """Get the current chat history."""
        return self.history

    def _save_history(self):
        """Save chat history to a JSON file."""
        history_dir = os.path.join("data", "chat_history")
        os.makedirs(history_dir, exist_ok=True)
        history_path = os.path.join(history_dir, f"{self.session_id}.json")
        
        with open(history_path, 'w') as f:
            json.dump(self.history, f, indent=2)

    def answer_question_with_context(self, user_question):
        """Generate an answer to a user's question and return both the answer and context."""
        # Add user message to history
        self.history.append({"role": "user", "content": user_question, "timestamp": datetime.now().isoformat()})
        
        # Retrieve relevant documents
        documents = self.retriever.retrieve(user_question, top_k=20)
        
        # Check if any documents were retrieved
        if not documents:
            answer = self._generate_no_info_response(user_question)
            return answer, []
        else:
            # Format retrieved documents as context
            context = json.dumps(documents)
            
            # Create prompt with context (your existing code)
            system_prompt = f"""
            You are an expert cheese sommelier and product specialist. Answer the user's question using the provided cheese information in comprehensive detail.
            
            CHEESE INFORMATION:
            {context}
            
            IMPORTANT INSTRUCTIONS:
            1. Always include ALL cheese products in your response that are relevant
            2. Create a separate section for EACH product with its own details
            3. For each product, include a complete product overview
            4. Format your response in a clean, organized way with clear sections
            
            Include:
            - Product details (name, brand, price, etc.)
            - Flavor profiles and characteristics
            - Usage recommendations
            - Images and shopping links when available
            """
            
            # Generate response
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_question}
                ],
                temperature=0.7
            )
            
            answer = response.choices[0].message.content
        
        # Add assistant response to history
        self.history.append({"role": "assistant", "content": answer, "timestamp": datetime.now().isoformat()})
        
        # Save history
        self._save_history()
        
        return answer, documents
# Example usage
if __name__ == "__main__":
    llm = LLM()
    answer = llm.answer_question("I want to buy white cheese good for pizza and which is expensive than $10 per each")
    print(answer)