import os
from pinecone import Pinecone, ServerlessSpec
from dotenv import load_dotenv
from openai import OpenAI
import yaml

def load_config():
    with open('config/config.yaml', 'r') as file:
        return yaml.safe_load(file)

def create_pinecone_index():
    """Create a new Pinecone index if it doesn't exist"""
    # Load environment variables and configuration
    load_dotenv()
    config = load_config()
    
    # Initialize Pinecone client
    pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
    
    # Get index settings from config
    index_name = config['vector_db']['pinecone']['index_name']
    dimension = config['vector_db']['pinecone']['dimension']
    metric = config['vector_db']['pinecone']['metric']
    cloud = config['vector_db']['pinecone']['cloud']
    region = config['vector_db']['pinecone']['region']
    
    # Check if index exists and create if needed
    if index_name not in pc.list_indexes().names():
        pc.create_index(
            name=index_name,
            dimension=dimension,
            metric=metric,
            spec=ServerlessSpec(cloud=cloud, region=region)
        )
        print(f"Created new Pinecone index: {index_name}")
    else:
        print(f"Using existing Pinecone index: {index_name}")
    
    # Return the index
    return pc.Index(index_name)

def upsert_to_pinecone(processed_data, batch_size=None):
    """Upsert processed data to Pinecone in batches"""
    # Load environment variables and configuration
    load_dotenv()
    config = load_config()
    
    # Get batch size from config or use provided value
    if batch_size is None:
        batch_size = config['vector_db']['embeddings']['batch_size']
    
    # Initialize OpenAI client
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    
    # Get or create Pinecone index
    index = create_pinecone_index()
    
    # Process in batches
    for i in range(0, len(processed_data), batch_size):
        batch = processed_data[i:i+batch_size]
        
        texts = [item['text'] for item in batch]
        metadata_list = [item['metadata'] for item in batch]
        ids = [f"cheese_{i+idx}" for idx in range(len(batch))]
        
        # Create embeddings
        response = client.embeddings.create(
            input=texts,
            model=config['vector_db']['embeddings']['model']
        )
        
        embeddings = [item.embedding for item in response.data]
        
        # Prepare vectors for upsert
        vectors = []
        for j in range(len(embeddings)):
            vectors.append({
                "id": ids[j],
                "values": embeddings[j],
                "metadata": metadata_list[j]
            })
        
        # Upsert to Pinecone
        index.upsert(vectors=vectors)
        print(f"Processed and uploaded batch {i//batch_size + 1}/{(len(processed_data) + batch_size - 1)//batch_size}")
    
    print("Vector database updated successfully!")
    return index

def search_cheeses(query, top_k=5):
    """Search for cheeses matching the query"""
    # Load environment variables and configuration
    load_dotenv()
    config = load_config()
    
    # Initialize OpenAI client
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    
    # Get Pinecone index
    pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
    index = pc.Index(config['vector_db']['pinecone']['index_name'])
    
    # Create query embedding
    query_response = client.embeddings.create(
        input=[query],
        model=config['vector_db']['embeddings']['model']
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
