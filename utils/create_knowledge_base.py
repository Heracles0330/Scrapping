import os
import sys
import json
import yaml
from pathlib import Path

# Add src to the Python path
sys.path.append(os.path.abspath('src'))

# Import knowledge base modules
from knowledge_base import process_cheese_data, create_pinecone_index, upsert_to_pinecone

def main():
    # Ensure config directory exists
    os.makedirs('config', exist_ok=True)
    
    # Load configuration
    with open('config/config.yaml', 'r') as file:
        config = yaml.safe_load(file)
    
    # Load processed cheese data
    data_path = 'data/image-processed/cheese_data_with_image_descriptions.json'
    with open(data_path, 'r') as f:
        cheese_data = json.load(f)
    
    print(f"Loaded {len(cheese_data)} cheese products from {data_path}")
    
    # Process the data
    print("Processing data with enhanced metadata...")
    processed_data = process_cheese_data(cheese_data)
    
    # Create/get Pinecone index
    print("Setting up Pinecone vector database...")
    create_pinecone_index()
    
    # Upsert data to Pinecone
    print("Uploading vectors to Pinecone...")
    upsert_to_pinecone(processed_data, batch_size=config['vector_db']['embeddings']['batch_size'])
    
    print("Knowledge base creation complete!")

if __name__ == "__main__":
    main()
