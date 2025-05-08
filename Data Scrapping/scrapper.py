import json
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pandas as pd
import os
import subprocess
import re

def scrape_with_selenium(url,driver):
    
    driver.get(url)
    
    # Wait for the page to load
    time.sleep(3)
    
    # Extract product details
    product_data = {
        'url': url,
        'title': '',
        'brand': '',
        'sku': '',
        'upc': '',
        'image_urls': [],
        'case_price': '',
        'each_price': '',
        'case_pack_size': '',
        'each_pack_size':'',
        'case_weight': '',
        'each_weight': '',
        'case_dimensions': '',
        'each_dimensions': '',
        'price_per_unit': '',
        'category': [],
        'related_items': [],
        'others_you_may_like_urls': []  # Changed to just store URLs
    }
    
    # Get title
    try:
        title = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "h1.chakra-heading"))
        )
        product_data['title'] = title.text

        description = driver.find_element(By.CSS_SELECTOR, "div.css-ahthbn div.css-0")
        upc_match = re.search(r'UPC:?\s*(\d+)', description.text, re.IGNORECASE)
        if upc_match:
            product_data['upc'] = upc_match.group(1)
        sku_match = re.search(r'SKU:?\s*(\d+)', description.text, re.IGNORECASE)
        if sku_match:
            product_data['sku'] = sku_match.group(1)
    except:
        pass
    
    # Get brand
    try:
        brand_selectors = ["p.chakra-text.css-drbcjm", "div.chakra-stack > p.chakra-text:first-of-type"]
        for selector in brand_selectors:
            try:
                brand = driver.find_element(By.CSS_SELECTOR, selector)
                if brand and len(brand.text.strip()) < 50:  # Avoid getting long text
                    product_data['brand'] = brand.text.strip()
                    break
            except:
                continue
    except:
        pass
    
    
    # Get categories
    try:
        breadcrumbs = driver.find_elements(By.CSS_SELECTOR, ".chakra-breadcrumb__list li a")
        product_data['category'] = [crumb.text for crumb in breadcrumbs]
    except:
        pass
    
    # Get table information
    try:
        tableinfos = driver.find_elements(By.CSS_SELECTOR, "td.css-1eyncsv")
        # print(tableinfos[0].text)
        if len(tableinfos) == 6:
            product_data['case_pack_size'] = tableinfos[0].text
            product_data['each_pack_size'] = tableinfos[1].text
            product_data['case_weight'] = tableinfos[4].text
            product_data['each_weight'] = tableinfos[5].text
            product_data['case_dimensions'] = tableinfos[2].text
            product_data['each_dimensions'] = tableinfos[3].text
        elif len(tableinfos) == 3:
            product_data['each_pack_size'] = tableinfos[0].text
            product_data['each_dimensions'] = tableinfos[1].text
            product_data['each_weight'] = tableinfos[2].text
    except:
        pass
    #Get price information
    
    try:
        priceInfo = driver.find_elements(By.CSS_SELECTOR, "div.css-1ktp5rg b")
        if len(priceInfo) == 2:
            product_data['case_price'] = priceInfo[0].text
            product_data['each_price'] = priceInfo[1].text
        elif len(priceInfo) == 1:
            product_data['each_price'] = priceInfo[0].text
    except:
        pass

    try:
        badge = driver.find_element(By.CSS_SELECTOR, "span.chakra-badge.css-1mwp5d1")
        product_data['price_per_unit'] = badge.text
    except:
        pass
    
    # Get all product images
    try:
        # First click on the tabs to make sure all images are loaded
        image_tabs = driver.find_elements(By.CSS_SELECTOR, ".chakra-tabs__tab")
        for tab in image_tabs:
            try:
                driver.execute_script("arguments[0].click();", tab)
                time.sleep(0.5)  # Short pause to let images load
            except:
                pass
        
        # Now collect the image URLs
        image_elements = driver.find_elements(By.CSS_SELECTOR, "div[role='tabpanel'] img")
        for img in image_elements:
            try:
                src = img.get_attribute('src')
                if src and src not in product_data['image_urls']:
                    product_data['image_urls'].append(src)
            except:
                continue
    except:
        pass
    
    # Get related items (specifically "Related Items" section)
    try:
        related_items = []
        
        # Find the "Related Items" heading
        related_heading = None
        headings = driver.find_elements(By.XPATH, "//h4[contains(text(), 'Related items') or contains(text(), 'Related Items')]")
        if headings:
            related_heading = headings[0]
        
        if related_heading:
            # Using JavaScript to get the proper container for related items
            # First find the container with the heading
            related_container = driver.execute_script("""
                var heading = arguments[0];
                var container = heading.closest('.css-1811skr') || heading.closest('.css-2xph3x') || heading.closest('div[class*="css"]');
                return container;
            """, related_heading)
            
            if related_container:
                # Find just the product cards in this specific container
                product_cards = related_container.find_elements(By.CSS_SELECTOR, "a.chakra-card[role='link']")
                
                # When we don't find any directly under the container, try finding them in a child container
                if not product_cards:
                    product_cards = related_container.find_elements(By.CSS_SELECTOR, "div.css-0 a.chakra-card[role='link']")
                
                # If still none, try another approach - look for cards in the same section as the heading
                if not product_cards:
                    # Look for the closest parent div that might contain the cards
                    related_section = driver.execute_script("""
                        var heading = arguments[0];
                        var section = heading.parentElement;
                        while (section && !section.querySelector('a.chakra-card[role="link"]') && section.tagName !== 'BODY') {
                            section = section.parentElement;
                        }
                        return section;
                    """, related_heading)
                    
                    if related_section:
                        product_cards = related_section.find_elements(By.CSS_SELECTOR, "a.chakra-card[role='link']")
                
                # Process the found cards
                for card in product_cards:
                    try:
                        product_url = card.get_attribute('href')
                        
                        # Get product name
                        name_elem = None
                        try:
                            name_elem = card.find_element(By.CSS_SELECTOR, "p.chakra-text[class*='css-']")
                        except:
                            try:
                                # Try alternative selector
                                name_elem = card.find_element(By.CSS_SELECTOR, "p.chakra-text")
                            except:
                                pass
                        
                        product_name = name_elem.text.strip() if name_elem else ''
                        
                        # Get brand - usually second p.chakra-text
                        product_brand = ''
                        try:
                            text_elements = card.find_elements(By.CSS_SELECTOR, "p.chakra-text")
                            if len(text_elements) > 1:
                                product_brand = text_elements[1].text.strip()
                        except:
                            pass
                        
                        # Get price
                        product_price = ''
                        try:
                            price_elem = card.find_element(By.CSS_SELECTOR, "b.chakra-text")
                            product_price = price_elem.text.strip()
                        except:
                            pass
                        
                        # Only add if we have at least a URL
                        if product_url:
                            related_items.append({
                                'name': product_name,
                                'brand': product_brand,
                                'price': product_price,
                                'url': product_url
                            })
                    except Exception as e:
                        print(f"Error extracting related item: {e}")
                        continue
        
        # Special handling for this specific page
        # If we know this page has exactly 2 related items but we didn't find them,
        # look for the first 2 items in the first product card container
        if len(related_items) == 0:
            print("Using backup method to find related items")
            try:
                # Try to find the container with product cards
                card_containers = driver.find_elements(By.CSS_SELECTOR, "div.-mx-2, div.css-1ydflst")
                if card_containers:
                    # Take the first container which should have the 2 related items
                    product_cards = card_containers[0].find_elements(By.CSS_SELECTOR, "a.chakra-card[role='link']")
                    # Limit to the first 2 cards which should be the related items
                    product_cards = product_cards[:2] if len(product_cards) >= 2 else product_cards
                    
                    for card in product_cards:
                        product_url = card.get_attribute('href')
                        
                        # Get product name
                        name_elem = card.find_element(By.CSS_SELECTOR, "p.chakra-text")
                        product_name = name_elem.text.strip() if name_elem else ''
                        
                        # Get brand - usually second p.chakra-text
                        product_brand = ''
                        text_elements = card.find_elements(By.CSS_SELECTOR, "p.chakra-text")
                        if len(text_elements) > 1:
                            product_brand = text_elements[1].text.strip()
                        
                        # Get price
                        product_price = ''
                        price_elem = card.find_element(By.CSS_SELECTOR, "b.chakra-text")
                        product_price = price_elem.text.strip() if price_elem else ''
                        
                        if product_url:
                            related_items.append({
                                'name': product_name,
                                'brand': product_brand,
                                'price': product_price,
                                'url': product_url
                            })
            except Exception as e:
                print(f"Error using backup method: {e}")
        
        product_data['related_items'] = related_items
    except Exception as e:
        print(f"Error extracting related items: {e}")
    
    # CHANGED: Get only URLs for "Others you may like" products
    try:
        others_you_may_like_urls = []
        
        # Get all product URLs first
        related_urls = [item['url'] for item in product_data['related_items'] if 'url' in item]
        
        # Look for products in the main carousel/slider
        product_cards = driver.find_elements(By.CSS_SELECTOR, ".slick-track a.chakra-card[role='link']")
        
        # If carousel not found, try other common containers
        if not product_cards:
            product_cards = driver.find_elements(By.CSS_SELECTOR, ".swiper-wrapper a.chakra-card[role='link']")
        
        # If still not found, look for any product cards outside the Related Items section
        if not product_cards:
            all_cards = driver.find_elements(By.CSS_SELECTOR, "a.chakra-card[role='link']")
            # Filter out cards that are already in related_items
            product_cards = [card for card in all_cards if card.get_attribute('href') not in related_urls]
        
        for card in product_cards:
            try:
                product_url = card.get_attribute('href')
                
                # Skip if this product was already in related_items
                if product_url in related_urls:
                    continue
                
                # Only add URLs that we haven't seen yet
                if product_url and product_url not in others_you_may_like_urls:
                    others_you_may_like_urls.append(product_url)
            except:
                continue
        
        product_data['others_you_may_like_urls'] = others_you_may_like_urls
    except:
        pass
    
    
    return product_data

def scrape_cheese_data():
    # Set up Selenium with Chrome
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    
    # Installation and setup for chromedriver
    try:
        # Check if Chrome is installed
        subprocess.run(["google-chrome", "--version"], check=True, stdout=subprocess.PIPE)
    except:
        print("Installing Chrome...")
        subprocess.run(["apt-get", "update"])
        subprocess.run(["apt-get", "install", "-y", "google-chrome-stable"])
    
    # Use Selenium Wire with Chrome directly
    driver = webdriver.Chrome(options=chrome_options)
    wait = WebDriverWait(driver, 10)
    
    try:
        all_product_links = []
        page_num = 1
        has_next_page = True
        
        while has_next_page:
            print(f"Scraping page {page_num}...")
            url = f'https://shop.kimelo.com/department/cheese/3365?page={page_num}'
            driver.get(url)
            
            # Wait for page to load completely
            time.sleep(5)
            
            # Wait for products to load
            try:
                wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "a.chakra-card.group")))
                
                # Get all product cards
                product_cards = driver.find_elements(By.CSS_SELECTOR, "a.chakra-card.group")
                
                # Extract links
                page_links = [card.get_attribute('href') for card in product_cards if card.get_attribute('href')]
                all_product_links.extend(page_links)
                
                print(f"Found {len(page_links)} products on page {page_num}")
                
                # Check if there's a next page
                next_buttons = driver.find_elements(By.CSS_SELECTOR, "a[aria-label='Next page']")
                if next_buttons and not next_buttons[0].get_attribute("disabled"):
                    page_num += 1
                else:
                    has_next_page = False
                    
            except Exception as e:
                print(f"Error on page {page_num}: {e}")
                has_next_page = False
        
        print(f"Found a total of {len(all_product_links)} product links across {page_num} pages")
        
        # Now scrape individual product pages
        cheese_data = []
        
        for link in all_product_links:
            try:
                print(f"Scraping product: {link}")
                product_info = scrape_with_selenium(link,driver)
                
                cheese_data.append(product_info)
                
            except Exception as e:
                print(f"Error scraping {link}: {e}")
        
        # Save data to JSON and CSV
        with open('cheese_data.json', 'w') as f:
            json.dump(cheese_data, f, indent=2)
        
        # Convert to DataFrame and save as CSV
        df = pd.json_normalize(cheese_data)
        df.to_csv('cheese_data.csv', index=False)
        
        print(f"Successfully scraped {len(cheese_data)} cheese products!")
        return cheese_data
        
    except Exception as e:
        print(f"Error during scraping: {e}")
        raise
    finally:
        driver.quit()

if __name__ == "__main__":
    scrape_cheese_data()