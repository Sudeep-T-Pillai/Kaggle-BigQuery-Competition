#!/usr/bin/env python3
"""
Product Image Fetcher Script - Web Scraping Version
Fetches real product images using web scraping (no API keys required)
"""

import requests
import json
import csv
import time
import os
import re
from urllib.parse import quote_plus, urljoin, urlparse
from typing import Dict, List, Optional, Tuple
import random
from dataclasses import dataclass
from bs4 import BeautifulSoup
import base64

@dataclass
class ProductImage:
    name: str
    image_url: str
    source: str
    alt_text: str = ""

class ProductImageFetcher:
    def __init__(self, delay_range: Tuple[float, float] = (3.0, 6.0)):
        self.delay_range = delay_range
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
        
        # Common image file extensions
        self.image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp'}
        
    def clean_product_name(self, name: str) -> str:
        """Clean product name for better search results"""
        # Remove common prefixes/suffixes that might confuse search
        cleaned = re.sub(r'^(Set Of \d+|Large|Medium|Small)\s+', '', name, flags=re.IGNORECASE)
        cleaned = re.sub(r'\s+(Design|Style|Holder|Metal|Sign)$', '', cleaned, flags=re.IGNORECASE)
        return cleaned.strip()
    
    def search_bing_images(self, product_name: str) -> Optional[str]:
        """Search Bing Images (more permissive than Google)"""
        try:
            query = quote_plus(f"{product_name} product buy shopping")
            url = f"https://www.bing.com/images/search?q={query}&form=HDRSC2&first=1&tsc=ImageHoverTitle"
            
            response = self.session.get(url, timeout=15)
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Look for image elements
                img_elements = soup.find_all('img', {'src': True})
                for img in img_elements:
                    src = img.get('src', '')
                    if src and any(ext in src.lower() for ext in self.image_extensions):
                        if 'http' in src and 'bing.com' not in src:
                            return src
                
                # Alternative: look for data attributes
                img_containers = soup.find_all('a', {'class': 'm'})
                for container in img_containers[:3]:  # Check first 3
                    m_attr = container.get('m', '')
                    if m_attr:
                        try:
                            import json
                            data = json.loads(m_attr)
                            if 'murl' in data:
                                return data['murl']
                        except:
                            continue
                            
        except Exception as e:
            print(f"Bing search failed for {product_name}: {e}")
        return None
    
    def search_duckduckgo_images(self, product_name: str) -> Optional[str]:
        """Search DuckDuckGo Images (no rate limiting)"""
        try:
            # First get the search page
            query = quote_plus(f"{product_name}")
            search_url = f"https://duckduckgo.com/?q={query}&iax=images&ia=images"
            
            response = self.session.get(search_url, timeout=15)
            if response.status_code == 200:
                # Look for vqd token needed for image search
                vqd_match = re.search(r'vqd="([^"]+)"', response.text)
                if not vqd_match:
                    return None
                
                vqd = vqd_match.group(1)
                
                # Now get actual images
                img_url = "https://duckduckgo.com/i.js"
                params = {
                    'l': 'us-en',
                    'o': 'json',
                    'q': product_name,
                    'vqd': vqd,
                    'f': ',,,',
                    'p': '1',
                    'v7exp': 'a'
                }
                
                img_response = self.session.get(img_url, params=params, timeout=15)
                if img_response.status_code == 200:
                    try:
                        data = img_response.json()
                        if 'results' in data and data['results']:
                            for result in data['results'][:3]:  # Try first 3
                                if 'image' in result:
                                    return result['image']
                    except json.JSONDecodeError:
                        pass
                        
        except Exception as e:
            print(f"DuckDuckGo search failed for {product_name}: {e}")
        return None
    
    def search_shopping_sites(self, product_name: str) -> Optional[str]:
        """Search common shopping sites for product images"""
        shopping_sites = [
            {
                'name': 'Amazon',
                'url': f"https://www.amazon.com/s?k={quote_plus(product_name)}",
                'img_selector': '.s-image'
            },
            {
                'name': 'eBay', 
                'url': f"https://www.ebay.com/sch/i.html?_nkw={quote_plus(product_name)}",
                'img_selector': '.s-item__image img'
            }
        ]
        
        for site in shopping_sites:
            try:
                response = self.session.get(site['url'], timeout=15)
                if response.status_code == 200:
                    soup = BeautifulSoup(response.content, 'html.parser')
                    imgs = soup.select(site['img_selector'])
                    
                    for img in imgs[:3]:  # Try first 3 images
                        src = img.get('src') or img.get('data-src')
                        if src and 'http' in src and any(ext in src.lower() for ext in self.image_extensions):
                            # Skip very small images
                            if 'thumb' not in src.lower() and '50x50' not in src:
                                return src
                                
            except Exception as e:
                print(f"Shopping site search failed for {site['name']}: {e}")
                continue
        
        return None
    
    def search_direct_product_search(self, product_name: str) -> Optional[str]:
        """Direct product search on image hosting sites"""
        try:
            # Search Wikimedia Commons for similar items
            query = quote_plus(product_name.replace(' ', '_'))
            commons_url = f"https://commons.wikimedia.org/w/api.php"
            params = {
                'action': 'query',
                'format': 'json',
                'list': 'search',
                'srsearch': product_name,
                'srnamespace': '6',  # File namespace
                'srlimit': '3'
            }
            
            response = self.session.get(commons_url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if 'query' in data and 'search' in data['query']:
                    for result in data['query']['search']:
                        title = result['title'].replace('File:', '')
                        img_url = f"https://commons.wikimedia.org/wiki/Special:FilePath/{quote_plus(title)}"
                        return img_url
                        
        except Exception as e:
            print(f"Wikimedia search failed for {product_name}: {e}")
        
        return None
    
    def generate_smart_placeholder(self, product_name: str) -> str:
        """Generate a themed placeholder that looks like a real product image"""
        # Create a more sophisticated placeholder URL
        text = re.sub(r'[^\w\s-]', '', product_name)
        text = re.sub(r'[\s_-]+', '+', text)[:25]
        
        # Product category colors and themes
        themes = {
            'kitchen': {'bg': '2C3E50', 'text': 'ECF0F1', 'icon': '🍳'},
            'storage': {'bg': '3498DB', 'text': 'FFFFFF', 'icon': '📦'},
            'christmas': {'bg': 'C0392B', 'text': 'FFFFFF', 'icon': '🎄'},
            'toy': {'bg': 'F39C12', 'text': 'FFFFFF', 'icon': '🧸'},
            'bottle': {'bg': '8E44AD', 'text': 'FFFFFF', 'icon': '🍼'},
            'home': {'bg': '27AE60', 'text': 'FFFFFF', 'icon': '🏠'},
            'tea': {'bg': '16A085', 'text': 'FFFFFF', 'icon': '☕'},
            'metal': {'bg': '7F8C8D', 'text': 'FFFFFF', 'icon': '🔧'},
        }
        
        # Determine theme based on product name
        theme = themes['home']  # default
        product_lower = product_name.lower()
        
        for category, style in themes.items():
            keywords = {
                'kitchen': ['mug', 'tea', 'coffee', 'sugar', 'dispenser', 'jar', 'cake', 'tin'],
                'storage': ['storage', 'box', 'crate', 'tin', 'holder', 'container'],
                'christmas': ['christmas', 'star', 'stocking', 'xmas'],
                'toy': ['toy', 'dolly', 'spaceboy', 'bubbles', 'children'],
                'bottle': ['bottle', 'water', 'hot'],
                'home': ['door', 'wall', 'clock', 'sign', 'hanger'],
                'tea': ['tea', 'coffee'],
                'metal': ['metal', 'sign', 'zinc', 'wire']
            }
            
            if category in product_lower or any(word in product_lower for word in keywords.get(category, [])):
                theme = style
                break
        
        return f"https://via.placeholder.com/400x300/{theme['bg']}/{theme['text']}?text={quote_plus(text)}"
    
    def fetch_product_image(self, product_name: str) -> ProductImage:
        """Fetch image for a single product with multiple search methods"""
        print(f"Searching for: {product_name}")
        
        cleaned_name = self.clean_product_name(product_name)
        image_url = None
        source = "placeholder"
        
        # Try different search methods in order of reliability
        search_methods = [
            ("DuckDuckGo", self.search_duckduckgo_images),
            ("Bing Images", self.search_bing_images),
            ("Shopping Sites", self.search_shopping_sites),
            ("Direct Search", self.search_direct_product_search),
        ]
        
        for method_name, method in search_methods:
            try:
                image_url = method(cleaned_name)
                if image_url and self.validate_image_url(image_url):
                    source = method_name.lower().replace(' ', '_')
                    print(f"  ✓ Found image via {method_name}")
                    break
                elif image_url:
                    print(f"  ⚠ Found URL via {method_name} but validation failed")
            except Exception as e:
                print(f"  ✗ {method_name} failed: {e}")
                continue
        
        # If no real image found, use smart placeholder
        if not image_url:
            image_url = self.generate_smart_placeholder(product_name)
            source = "smart_placeholder"
            print(f"  → Using themed placeholder")
        
        return ProductImage(
            name=product_name,
            image_url=image_url,
            source=source,
            alt_text=f"Image of {product_name}"
        )
    
    def validate_image_url(self, url: str) -> bool:
        """Validate that URL points to an actual image"""
        try:
            # Quick HEAD request to check if image exists
            response = self.session.head(url, timeout=10)
            content_type = response.headers.get('content-type', '').lower()
            
            return (response.status_code == 200 and 
                   ('image' in content_type or 
                    any(ext in url.lower() for ext in self.image_extensions)))
        except:
            return False
    
    def fetch_all_images(self, product_names: List[str]) -> List[ProductImage]:
        """Fetch images for all products with rate limiting"""
        results = []
        total = len(product_names)
        
        print(f"Starting to fetch images for {total} products...\n")
        
        for i, product_name in enumerate(product_names, 1):
            print(f"[{i}/{total}] ", end="")
            
            try:
                product_image = self.fetch_product_image(product_name.strip())
                results.append(product_image)
                
                # Rate limiting - longer delays to be respectful
                if i < total:
                    delay = random.uniform(*self.delay_range)
                    print(f"  Waiting {delay:.1f}s...")
                    time.sleep(delay)
                    
            except Exception as e:
                print(f"  ✗ Error processing {product_name}: {e}")
                # Add a placeholder entry for failed products
                results.append(ProductImage(
                    name=product_name,
                    image_url=self.generate_smart_placeholder(product_name),
                    source="error_placeholder",
                    alt_text=f"Placeholder for {product_name}"
                ))
        
        return results
    
    def save_to_csv(self, products: List[ProductImage], filename: str = "product_images.csv"):
        """Save results to CSV file"""
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['product_name', 'image_url', 'source', 'alt_text']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            writer.writeheader()
            for product in products:
                writer.writerow({
                    'product_name': product.name,
                    'image_url': product.image_url,
                    'source': product.source,
                    'alt_text': product.alt_text
                })
        
        print(f"\n✓ Results saved to {filename}")
    
    def save_to_json(self, products: List[ProductImage], filename: str = "product_images.json"):
        """Save results to JSON file"""
        data = []
        for product in products:
            data.append({
                'product_name': product.name,
                'image_url': product.image_url,
                'source': product.source,
                'alt_text': product.alt_text
            })
        
        with open(filename, 'w', encoding='utf-8') as jsonfile:
            json.dump(data, jsonfile, indent=2, ensure_ascii=False)
        
        print(f"✓ Results saved to {filename}")


def main():
    # Product list from your data
    products = [
        "Set Of 2 Wooden Market Crates",
        "Christmas Star Wish List Chalkboard",
        "Storage Tin Vintage Leaf",
        "Tree T-Light Holder Willie Winkie",
        "Set Of 4 Knick Knack Tins Poppies",
        "Bag 500g Swirly Marbles",
        "Joy Wooden Block Letters",
        "Peace Wooden Block Letters",
        "T-Light Holder Hanging Lace",
        "T-Light Holder White Lace",
        "Toy Tidy Spaceboy",
        "Grow Your Own Flowers Set Of 3",
        "Toy Tidy Dolly Girl Design",
        "Set Of 3 Cake Tins Sketchbook",
        "Set Of 6 Herb Tins Sketchbook",
        "Squarecushion Cover Pink Union Jack",
        "36 Foil Star Cake Cases",
        "Triple Wire Hook Pink Heart",
        "36 Foil Heart Cake Cases",
        "Wood Stocking Christmas Scandispot",
        "Pantry Magnetic Shopping List",
        "Sketchbook Magnetic Shopping List",
        "Bull Dog Bottle Opener",
        "Classic Cafe Sugar Dispenser",
        "Small Ceramic Top Storage Jar",
        "Medium Ceramic Top Storage Jar",
        "Large Ceramic Top Storage Jar",
        "Travel Card Wallet Pantry",
        "Travel Card Wallet Skulls",
        "Travel Card Wallet Transport",
        "Travel Card Wallet Keep Calm",
        "Travel Card Wallet Retrospot",
        "Hot Water Bottle I Am So Poorly",
        "Alarm Clock Bakelike Ivory",
        "Alarm Clock Bakelike Pink",
        "Alarm Clock Bakelike Red",
        "Alarm Clock Bakelike Green",
        "Set Of 3 Cake Tins Pantry Design",
        "Grow A Flytrap Or Sunflower In Tin",
        "French Wc Sign Blue Metal",
        "Recipe Box Retrospot",
        "Recipe Box Pantry Yellow Design",
        "Circus Parade Lunch Box",
        "Picnic Boxes Set Of 3 Retrospot",
        "Gumball Coat Rack",
        "Popcorn Holder",
        "Hot Water Bottle Tea And Sympathy",
        "Chocolate Hot Water Bottle",
        "Chocolate This Way Metal Sign",
        "Gin And Tonic Mug",
        "Glamorous Mug",
        "Save The Planet Mug",
        "Retrospot Large Milk Jug",
        "Fawn Blue Hot Water Bottle",
        "White Skull Hot Water Bottle",
        "Door Hanger Mum + Dads Room",
        "Set 3 Retrospot Tea/Coffee/Sugar",
        "Please One Person Metal Sign",
        "Gin And Tonic Diet Metal Sign",
        "You're Confusing Me Metal Sign",
        "Toxic Area Door Hanger",
        "Moody Boy Door Hanger",
        "Moody Girl Door Hanger",
        "Red Retrospot Oven Glove",
        "Large Chinese Style Scissor",
        "Small Chinese Style Scissor",
        "Small Folding Scissor(Pointed Edge)",
        "Hand Over The Chocolate Sign",
        "Small Marshmallows Pink Bowl",
        "Small Dolly Mix Design Orange Bowl",
        "Set Of 4 English Rose Coasters",
        "N0 Singing Metal Sign",
        "Toilet Metal Sign",
        "Feng Shui Pillar Candle",
        "Tea Time Oven Glove",
        "English Rose Spirit Level",
        "Vintage Doily Travel Sewing Kit",
        "Blue Retro Kitchen Wall Clock",
        "Red Retro Kitchen Wall Clock",
        "Ivory Retro Kitchen Wall Clock",
        "Hot Stuff Hot Water Bottle",
        "Set Of 12 Fairy Cake Baking Cases",
        "Set Of Tea Coffee Sugar Tins Pantry",
        "Set Of 4 Knick Knack Tins Doily",
        "Doormat 3 Smiley Cats",
        "Hanging Metal Heart Lantern",
        "12 Pencils Tall Tube Skulls",
        "12 Pencils Tall Tube Woodland",
        "Gingham Recipe Book Box",
        "Egg Frying Pan Red",
        "Single Heart Zinc T-Light Holder",
        "Natural Slate Heart Chalkboard",
        "Heart Of Wicker Small",
        "Set Of 20 Vintage Christmas Napkins",
        "Antique Silver Tea Glass Engraved",
        "Playing Cards Keep Calm & Carry On",
        "Ice Cream Bubbles",
        "Wall Art Only One Person",
        "Childrens Cutlery Polkadot Blue",
        "Childrens Cutlery Polkadot Pink"
    ]
    
    print("=== Product Image Fetcher - Web Scraping Version ===")
    print("This version uses web scraping to find real product images:")
    print("- DuckDuckGo Images (no rate limits)")
    print("- Bing Images (more permissive)")
    print("- Shopping sites (Amazon, eBay)")
    print("- Wikimedia Commons")
    print("- Smart themed placeholders as fallbacks")
    print("\nNo API keys required! 🎉\n")
    
    # Initialize the fetcher with respectful delays
    fetcher = ProductImageFetcher(delay_range=(3.0, 6.0))
    
    # For testing, let's process first 99 products
    # Change to `products` for all items
    sample_products = products[:99]  # Increase this number or use `products` for all

    print(f"Processing {len(sample_products)} products (change sample_products to products for all items)\n")
    
    # Fetch images
    results = fetcher.fetch_all_images(sample_products)
    
    # Save results
    fetcher.save_to_csv(results, "product_images.csv")
    fetcher.save_to_json(results, "product_images.json")
    
    print(f"\n=== Summary ===")
    print(f"Total products processed: {len(results)}")
    real_images = sum(1 for r in results if 'placeholder' not in r.source)
    placeholders = sum(1 for r in results if 'placeholder' in r.source)
    print(f"Real images found: {real_images}")
    print(f"Placeholders used: {placeholders}")
    
    # Show sources breakdown
    sources = {}
    for result in results:
        sources[result.source] = sources.get(result.source, 0) + 1
    
    print(f"\nSources breakdown:")
    for source, count in sources.items():
        print(f"  {source}: {count}")

if __name__ == "__main__":
    # Install required packages if not present
    try:
        from bs4 import BeautifulSoup
    except ImportError:
        print("Installing required packages...")
        import subprocess
        subprocess.check_call(['pip', 'install', 'beautifulsoup4', 'requests'])
        from bs4 import BeautifulSoup
    
    main()