import os
import sys
import yaml
import json
from pathlib import Path

# Add src to the Python path
sys.path.append(os.path.abspath('src'))

# Import scraper modules
from scraper import scrape_cheese_data, process_images

def main():
    # Create required directories
    os.makedirs('data/raw', exist_ok=True)
    os.makedirs('data/processed', exist_ok=True)
    
    # Load configuration
    with open('config/config.yaml', 'r') as file:
        config = yaml.safe_load(file)
    
    print("Starting scraper...")
    
    # Step 1: Scrape cheese data
    print("Scraping cheese data from website...")
    cheese_data = scrape_cheese_data()
    
    # Save raw data
    raw_output_path = 'data/raw/cheese_data.json'
    with open(raw_output_path, 'w') as f:
        json.dump(cheese_data, f, indent=2)
    
    print(f"Raw data saved to {raw_output_path}")
    
    # Step 2: Process images
    print("Processing images to add descriptions...")
    processed_data = process_images(
        data_path=raw_output_path,
        output_path='data/processed/cheese_data_with_image_descriptions.json'
    )
    
    print(f"Processed data saved to data/processed/cheese_data_with_image_descriptions.json")
    print(f"Successfully scraped and processed {len(processed_data)} cheese products!")

if __name__ == "__main__":
    main()
