import json
from openai import OpenAI
import os
from dotenv import load_dotenv
import httpx
import urllib.parse
import yaml

class ImageProcessor:
    def __init__(self, config_path='config/config.yaml'):
        # Load configuration
        with open(config_path, 'r') as file:
            self.config = yaml.safe_load(file)
        
        # Load environment variables
        load_dotenv()
        
        # Initialize HTTP client
        self.http_client = httpx.Client()
        
        # Initialize OpenAI client
        self.client = OpenAI(
            api_key=os.getenv("OPENAI_API_KEY"),
            http_client=self.http_client
        )
    
    def get_original_image_url(self, next_js_url):
        """Extract the original image URL from a Next.js image URL"""
        # Parse the URL to get query parameters
        parsed_url = urllib.parse.urlparse(next_js_url)
        query_params = urllib.parse.parse_qs(parsed_url.query)
        
        # The original URL is in the 'url' parameter, URL-encoded
        if 'url' in query_params:
            original_url = query_params['url'][0]
            # Decode it
            decoded_url = urllib.parse.unquote(original_url)
            return decoded_url
        return None
    
    def get_image_description(self, image_url):
        original_url = self.get_original_image_url(image_url)
        try:
            response = self.client.chat.completions.create(
                model=self.config['image_processing']['model'],
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": self.config['image_processing']['prompt']},
                            {"type": "image_url", "image_url": {"url": original_url}}
                        ],
                    }
                ],
                max_tokens=self.config['image_processing']['max_tokens']
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"Error processing image: {e}")
            return "Description unavailable"

def process_images(data_path='data/raw/cheese_data.json', output_path='data/processed/cheese_data_with_image_descriptions.json'):
    """Process all images in the cheese data and add descriptions"""
    processor = ImageProcessor()
    
    # Load data
    with open(data_path, 'r') as f:
        cheese_data = json.load(f)
    
    # Process each cheese item
    for cheese in cheese_data:
        if cheese["image_urls"]:
            for image in cheese["image_urls"]:
                primary_image_url = image
                cheese["image_description"] = processor.get_image_description(primary_image_url)
                break  # Just process the first image for each cheese
        else:
            cheese["image_description"] = "No image available"
        
        # Print progress
        print(f"Processed: {cheese['title']}")
    
    # Save the updated data
    with open(output_path, 'w') as f:
        json.dump(cheese_data, f, indent=2)
    
    print("All images processed and descriptions added!")
    return cheese_data
