import os
from openai import OpenAI
from dotenv import load_dotenv
import yaml

def load_config():
    with open('config/config.yaml', 'r') as file:
        return yaml.safe_load(file)

def create_embeddings(texts):
    """Create embeddings for a list of texts using OpenAI's API"""
    # Load environment variables and configuration
    load_dotenv()
    config = load_config()
    
    # Initialize OpenAI client
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    
    # Get embeddings from OpenAI
    response = client.embeddings.create(
        input=texts,
        model=config['vector_db']['embeddings']['model']
    )
    
    # Return the embeddings
    return [item.embedding for item in response.data]
