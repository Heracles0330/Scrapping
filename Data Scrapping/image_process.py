import json
from openai import OpenAI
import os
from dotenv import load_dotenv
import httpx
import urllib.parse

# Load environment variables (you'll need to create a .env file with your OPENAI_API_KEY)
load_dotenv()



http_client = httpx.Client()

# Initialize OpenAI client with the custom httpx client
client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    http_client=http_client
)




with open('Data Scrapping/cheese_data.json', 'r') as f:
    cheese_data = json.load(f)

def get_original_image_url(next_js_url):
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


# Function to get image description using GPT-4 Vision
def get_image_description(image_url):
    original_url = get_original_image_url(image_url)
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",  # Use the appropriate model
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Please describe this cheese product in detail - include appearance, texture, and any visible characteristics that would help identify the type of cheese."},
                        {"type": "image_url", "image_url": {"url": original_url}}
                    ],
                }
            ],
            max_tokens=300
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"Error processing image: {e}")
        return "Description unavailable"

# Process each cheese item
for cheese in cheese_data:
    if cheese["image_urls"]:
        for image in cheese["image_urls"]:
            primary_image_url = image
            cheese["image_description"] = get_image_description(primary_image_url)
    else:
        cheese["image_description"] = "No image available"
    
    # Print progress
    print(f"Processed: {cheese['title']}")

# Save the updated data
with open('cheese_data_with_image_descriptions.json', 'w') as f:
    json.dump(cheese_data, f, indent=2)

print("All images processed and descriptions added!")
