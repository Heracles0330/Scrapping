# All the helper functions for metadata extraction
import yaml

def load_config():
    with open('config/config.yaml', 'r') as file:
        return yaml.safe_load(file)

def extract_keywords(title, description):
    """Extract important keywords from title and description"""
    # In production, use NLP to extract key terms
    keywords = []
    if "cheddar" in title.lower() or "cheddar" in description.lower():
        keywords.append("cheddar")
    if "mozzarella" in title.lower() or "mozzarella" in description.lower():
        keywords.append("mozzarella")
    # Add more keyword extraction logic
    return keywords

def extract_texture(description):
    """Extract texture information from description"""
    if not description:
        return "unknown"
    if "soft" in description.lower():
        return "soft"
    if "firm" in description.lower() or "hard" in description.lower():
        return "firm"
    if "creamy" in description.lower():
        return "creamy"
    if "crumbly" in description.lower():
        return "crumbly"
    # Add more texture extraction logic
    return "medium"

def extract_flavor_profile(description):
    """Extract flavor profile from description"""
    if not description:
        return "a mild, creamy flavor profile"
    if "sharp" in description.lower():
        return "a sharp, tangy flavor profile"
    if "mild" in description.lower():
        return "a mild, subtle flavor profile"
    if "nutty" in description.lower():
        return "a nutty, slightly sweet flavor profile"
    # Add more flavor extraction logic
    return "a balanced flavor profile typical of this cheese variety"

def suggest_pairings_based_on_category(categories):
    """Suggest pairings based on cheese category"""
    if not categories:
        return "crackers, fruit, or wine"
    
    if isinstance(categories, str):
        categories = [categories]
        
    if "Cheddar" in categories:
        return "apples, pears, bread, or a robust red wine"
    if "Mozzarella" in categories:
        return "tomatoes, basil, olive oil, or a light white wine"
    if "Parmesan" in categories:
        return "pasta dishes, salads, or a medium-bodied red wine"
    # Add more pairing suggestions
    return "crackers, fruit, bread, or wine depending on your preference"

def determine_melting_properties(title, description):
    """Determine if cheese is good for melting"""
    title_lower = title.lower()
    desc_lower = description.lower()
    
    melting_cheeses = ["mozzarella", "cheddar", "american", "monterey", "jack", "swiss", "gouda", "provolone"]
    
    for cheese in melting_cheeses:
        if cheese in title_lower or cheese in desc_lower:
            return f"Yes, this cheese is excellent for melting and works well in dishes like {suggest_melting_dishes(cheese)}"
    
    return "Based on the information available, it's difficult to determine its melting properties, but you could experiment with it in cooked dishes"

def suggest_melting_dishes(cheese_type):
    """Suggest dishes based on melting cheese type"""
    cheese_dishes = {
        "mozzarella": "pizza, lasagna, or grilled cheese sandwiches",
        "cheddar": "mac and cheese, burgers, or quiche",
        "american": "burgers, grilled cheese sandwiches, or quesadillas",
        "swiss": "fondue, hot sandwiches, or gratins",
        # Add more cheese-specific dishes
    }
    return cheese_dishes.get(cheese_type, "various hot dishes and sandwiches")

def extract_color(description):
    """Extract color information from cheese description"""
    if not description:
        return "unknown"
    
    description = description.lower()
    
    # Check for specific color mentions
    if "white" in description:
        return "white"
    if "yellow" in description or "golden" in description:
        return "yellow"
    if "orange" in description:
        return "orange"
    if "pale yellow" in description or "off-white" in description or "ivory" in description:
        return "pale yellow"
    if "cream" in description or "creamy" in description:
        return "cream"
    if "blue" in description:
        return "blue-veined"
    
    # Default colors based on common cheese words
    if "cheddar" in description:
        return "yellow to orange"
    if "mozzarella" in description:
        return "white"
    if "parmesan" in description:
        return "pale yellow"
    if "gouda" in description:
        return "yellow"
    if "swiss" in description:
        return "pale yellow"
    
    return "varied"

def suggest_use_cases(title, categories):
    """Suggest use cases based on cheese title and categories"""
    title_lower = title.lower() if title else ""
    
    # Convert categories to list if it's a string
    if isinstance(categories, str):
        categories = [categories]
    elif not categories:
        categories = []
    
    use_cases = []
    
    # Check title for specific cheese types
    if "mozzarella" in title_lower:
        use_cases.extend(["pizza", "caprese salad", "lasagna", "pasta dishes"])
    elif "cheddar" in title_lower:
        use_cases.extend(["sandwiches", "burgers", "mac and cheese", "soups"])
    elif "parmesan" in title_lower or "parmigiano" in title_lower:
        use_cases.extend(["pasta topping", "risotto", "caesar salad", "grating over dishes"])
    elif "ricotta" in title_lower:
        use_cases.extend(["lasagna", "cannoli", "cheesecake", "stuffed pasta"])
    elif "blue" in title_lower or "gorgonzola" in title_lower:
        use_cases.extend(["salad topping", "dips", "steak topping", "cheese boards"])
    elif "feta" in title_lower:
        use_cases.extend(["greek salad", "pastries", "roasted vegetables", "mediterranean dishes"])
    elif "american" in title_lower:
        use_cases.extend(["burgers", "grilled cheese", "sandwiches", "melting applications"])
    elif "swiss" in title_lower:
        use_cases.extend(["sandwiches", "fondue", "gratins", "quiche"])
    elif "cream cheese" in title_lower:
        use_cases.extend(["bagels", "cheesecake", "frosting", "dips"])
    elif "jack" in title_lower or "monterey" in title_lower:
        use_cases.extend(["mexican dishes", "quesadillas", "burgers", "sandwiches"])
    
    # Check categories
    for category in categories:
        category_lower = category.lower()
        if "shredded" in category_lower:
            use_cases.extend(["topping", "melting", "baking"])
        elif "sliced" in category_lower:
            use_cases.extend(["sandwiches", "burgers", "wraps"])
        elif "specialty" in category_lower:
            use_cases.extend(["cheese boards", "appetizers", "wine pairing"])
    
    # Remove duplicates and limit to a reasonable number
    unique_use_cases = list(set(use_cases))
    if not unique_use_cases:
        return "cheese boards, cooking, sandwiches, and various recipes"
    
    return ", ".join(unique_use_cases[:5])

def extract_origin(title, description):
    """Extract or infer cheese origin from title and description"""
    if not title and not description:
        return "unknown"
    
    title_lower = title.lower() if title else ""
    desc_lower = description.lower() if description else ""
    combined_text = title_lower + " " + desc_lower
    
    # Check for explicit mentions of origins
    if "italian" in combined_text or "italy" in combined_text:
        return "Italy"
    if "french" in combined_text or "france" in combined_text:
        return "France"
    if "swiss" in combined_text or "switzerland" in combined_text:
        return "Switzerland"
    if "greek" in combined_text or "greece" in combined_text:
        return "Greece"
    if "spanish" in combined_text or "spain" in combined_text:
        return "Spain"
    if "dutch" in combined_text or "holland" in combined_text or "netherlands" in combined_text:
        return "Netherlands"
    if "english" in combined_text or "england" in combined_text or "british" in combined_text:
        return "England"
    if "american" in combined_text or "usa" in combined_text or "united states" in combined_text:
        return "United States"
    
    # Infer from cheese types
    if "parmesan" in combined_text or "parmigiano" in combined_text or "mozzarella" in combined_text or "ricotta" in combined_text:
        return "Italy"
    if "brie" in combined_text or "camembert" in combined_text or "roquefort" in combined_text:
        return "France"
    if "feta" in combined_text:
        return "Greece"
    if "gouda" in combined_text or "edam" in combined_text:
        return "Netherlands"
    if "cheddar" in combined_text or "stilton" in combined_text:
        return "England"
    if "monterey" in combined_text or "jack" in combined_text or "american" in combined_text:
        return "United States"
    
    return "unknown"

def extract_milk_type(title, description):
    """Extract or infer milk type from title and description"""
    if not title and not description:
        return "unknown"
    
    title_lower = title.lower() if title else ""
    desc_lower = description.lower() if description else ""
    combined_text = title_lower + " " + desc_lower
    
    # Check for explicit mentions of milk types
    if "cow" in combined_text or "cow's milk" in combined_text:
        return "cow"
    if "goat" in combined_text or "goat's milk" in combined_text:
        return "goat"
    if "sheep" in combined_text or "sheep's milk" in combined_text or "ewe" in combined_text:
        return "sheep"
    if "buffalo" in combined_text or "buffalo milk" in combined_text:
        return "buffalo"
    if "plant-based" in combined_text or "vegan" in combined_text or "non-dairy" in combined_text:
        return "plant-based"
    
    # Infer from cheese types
    if "mozzarella" in combined_text and "buffalo" in combined_text:
        return "buffalo"
    if "feta" in combined_text:
        return "sheep and goat blend"
    if "roquefort" in combined_text:
        return "sheep"
    if "chevre" in combined_text:
        return "goat"
    if "pecorino" in combined_text:
        return "sheep"
    if "manchego" in combined_text:
        return "sheep"
    
    # Default to cow's milk as it's most common
    if any(cheese in combined_text for cheese in ["cheddar", "swiss", "american", "brie", "camembert", "parmesan", "gouda", "edam"]):
        return "cow"
    
    return "likely cow"

def suggest_storage(categories):
    """Suggest storage methods based on cheese category"""
    if not categories:
        return "in the refrigerator in its original packaging or wrapped in cheese paper"
    
    if isinstance(categories, str):
        categories = [categories]
    
    categories_lower = [cat.lower() for cat in categories]
    
    # Fresh cheeses need careful storage
    if any(cat in ["".join(c.lower() for c in cat) for cat in categories] for cat in ["fresh", "ricotta", "cottage", "cream"]):
        return "in the refrigerator in an airtight container and consumed within a week"
    
    # Soft-ripened cheeses
    if any(cat in "".join(c.lower() for c in cat) for cat in categories_lower for cat in ["brie", "camembert"]):
        return "in the refrigerator wrapped in cheese paper or wax paper, and brought to room temperature before serving"
    
    # Hard aged cheeses
    if any(cat in "".join(c.lower() for c in cat) for cat in categories_lower for cat in ["parmesan", "aged", "hard"]):
        return "in the refrigerator wrapped in cheese paper or wax paper, which allows it to breathe while preventing it from drying out"
    
    # Blue cheeses
    if any(cat in "".join(c.lower() for c in cat) for cat in categories_lower for cat in ["blue", "gorgonzola", "roquefort"]):
        return "in the refrigerator wrapped in foil to prevent the mold from spreading to other foods"
    
    # Default storage recommendation
    return "in the refrigerator in its original packaging or wrapped in cheese paper, and ideally brought to room temperature before serving"

def process_cheese_data(cheese_data):
    """Process cheese data to create enhanced conversational text and metadata"""
    processed_items = []
    
    for cheese in cheese_data:
        # Create a more conversational and comprehensive text representation
        conversational_text = f"""
        This is {cheese.get('title', 'a cheese product')}, a {', '.join(cheese.get('category', ['cheese'])) if isinstance(cheese.get('category'), list) else cheese.get('category', 'cheese')} from {cheese.get('brand', 'unknown brand')}.
        
        You can purchase it for {cheese.get('each_price', '') or cheese.get('case_price', 'various prices')} per {cheese.get('each_weight', '') or cheese.get('case_weight', 'unit')}.
        
        Physical description: {cheese.get('image_description', 'No image description available.')}
        
        Common questions about this product:
        Q: What does this cheese taste like?
        A: Based on the description, this {cheese.get('title', '').lower() if cheese.get('title') else 'cheese'} likely has {extract_flavor_profile(cheese.get('image_description', ''))}.
        
        Q: What can I pair this cheese with?
        A: This type of cheese would pair well with {suggest_pairings_based_on_category(cheese.get('category', []))}.
        
        Q: Is this cheese good for melting?
        A: {determine_melting_properties(cheese.get('title', ''), cheese.get('image_description', ''))}.
        
        Q: How should I store this cheese?
        A: Generally, this type of cheese should be stored {suggest_storage(cheese.get('category', []))}.
        """
        
        # Clean up the text
        conversational_text = ' '.join(conversational_text.split())
        
        # Enhanced metadata for better filtering and retrieval
        metadata_item = {
            # Include all original fields from the cheese data
            **cheese,  # This spreads all fields from the cheese object into metadata
            
            # Add the computed fields
            "keywords": extract_keywords(cheese.get("title", ""), cheese.get("image_description", "")),
            "texture": extract_texture(cheese.get("image_description", "")),
            "flavor_profile": extract_flavor_profile(cheese.get("image_description", "")),
            "color": extract_color(cheese.get("image_description", "")),
            "use_cases": suggest_use_cases(cheese.get("title", ""), cheese.get("category", [])),
            "origin": extract_origin(cheese.get("title", ""), cheese.get("image_description", "")),
            "milk_type": extract_milk_type(cheese.get("title", ""), cheese.get("image_description", "")),
        }
        
        # Convert non-string fields to strings for Pinecone metadata
        for key, value in metadata_item.items():
            if isinstance(value, list):
                if key == "image_urls" or key == "others_you_may_like_urls":
                    # For URL lists, join with comma
                    metadata_item[key] = ','.join(value) if value else ""
                elif key == "category":
                    # Keep category as is, handled separately below
                    pass
                elif key == "related_items":
                    # For objects, convert to string representation
                    metadata_item[key] = str(value)
                else:
                    # For regular lists, join with comma
                    metadata_item[key] = ','.join(str(item) for item in value) if value else ""
            elif isinstance(value, dict):
                # Convert dictionaries to string
                metadata_item[key] = str(value)
        
        # Handle category field separately for proper filtering
        if 'category' in cheese and cheese['category']:
            if isinstance(cheese['category'], list):
                metadata_item["category"] = cheese['category'][0] if cheese['category'] else ""
                if len(cheese['category']) > 1:
                    metadata_item["subcategory"] = cheese['category'][1]
                    metadata_item["all_categories"] = ','.join(cheese['category'])  # Store all categories as string
            else:
                metadata_item["category"] = cheese['category']
        
        processed_items.append({
            "text": conversational_text,
            "metadata": metadata_item
        })
    
    return processed_items
