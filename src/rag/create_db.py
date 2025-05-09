import sqlite3
import os
import json
import yaml
from pinecone import Pinecone
from dotenv import load_dotenv

def create_cheese_database():
    """Create a SQLite database for cheese metadata from Pinecone."""
    # Load environment variables and config
    load_dotenv()
    
    # Load configuration
    with open('config/config.yaml', 'r') as file:
        config = yaml.safe_load(file)
    
    # Create data directory if it doesn't exist
    os.makedirs('data', exist_ok=True)
    
    # Initialize database
    db_path = 'data/cheese.db'
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create table with all needed fields
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS cheese (
        id TEXT PRIMARY KEY,
        title TEXT,
        description TEXT,
        brand TEXT,
        origin TEXT,
        color TEXT,
        texture TEXT,
        price_per_unit REAL,
        case_price REAL,
        each_price REAL,
        each_weight REAL,
        case_weight REAL,
        milk_type TEXT,
        flavor_profile TEXT,
        sku TEXT,
        upc TEXT,
        image_urls TEXT,
        url TEXT,
        related_items TEXT,
        use_cases TEXT,
        vector_id TEXT,
        keywords TEXT
    )
    ''')
    
    # Connect to Pinecone
    pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
    index_name = config['vector_db']['pinecone']['index_name']
    index = pc.Index(index_name)
    
    print(f"Connected to Pinecone index: {index_name}")
    
    # Get all vector IDs from Pinecone
    stats = index.describe_index_stats()
    total_vectors = stats.total_vector_count
    print(f"Total vectors in Pinecone: {total_vectors}")
    
    # Fetch all vectors (for small datasets) or paginate for larger ones
    # This is a simplified approach - for very large datasets you'd need pagination
    try:
        # Query a small sample first to get IDs
        sample_results = index.query(
            vector=[0.1] * 1536,  # Dummy vector
            top_k=min(10000, total_vectors),
            include_metadata=True
        )
        
        # Process and insert data
        count = 0
        for match in sample_results.matches:
            metadata = match.metadata
            vector_id = match.id
            print(vector_id)
            # Extract all relevant fields, defaulting to appropriate empty values
            cursor.execute('''
            INSERT OR REPLACE INTO cheese VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                metadata.get('id', vector_id),
                metadata.get('title', ''),
                metadata.get('text', ''),
                metadata.get('brand', ''),
                metadata.get('origin', ''),
                metadata.get('color', ''),
                metadata.get('texture', ''),
                float(metadata.get('price_per_unit', 0.0) or 0.0),
                float(metadata.get('case_price', 0.0) or 0.0),
                float(metadata.get('each_price', 0.0) or 0.0),
                float(metadata.get('each_weight', 0.0) or 0.0),
                float(metadata.get('case_weight', 0.0) or 0.0),
                metadata.get('milk_type', ''),
                metadata.get('flavor_profile', ''),
                metadata.get('sku', ''),
                metadata.get('upc', ''),
                json.dumps(metadata.get('image_urls', [])),
                metadata.get('url', ''),
                json.dumps(metadata.get('related_items', [])),
                json.dumps(metadata.get('use_cases', [])),
                vector_id,
                json.dumps(metadata.get('keywords', []))
            ))
            
            count += 1
            if count % 100 == 0:
                print(f"Processed {count} records...")
        
        conn.commit()
        print(f"Successfully imported {count} records to SQLite database at {db_path}")
        
    except Exception as e:
        print(f"Error importing data: {e}")
        conn.rollback()
    
    finally:
        conn.close()

if __name__ == "__main__":
    create_cheese_database()
