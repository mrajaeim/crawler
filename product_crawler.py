import asyncio
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
import json
import re
import logging
import argparse
import os
from urllib.parse import urlparse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("crawler.log"),
        logging.StreamHandler()
    ]
)

class ProductCrawler:
    def __init__(self):
        self.browser = None
        self.context = None
        self.page = None
    
    async def initialize(self):
        """Initialize the Playwright browser"""
        playwright = await async_playwright().start()
        self.browser = await playwright.chromium.launch(headless=True)
        self.context = await self.browser.new_context()
        self.page = await self.context.new_page()
    
    async def close(self):
        """Close the browser and clean up resources"""
        if self.browser:
            await self.browser.close()
    
    async def crawl_url(self, url):
        """Crawl a specific URL and extract product information if it's a product page"""
        try:
            logging.info(f"Crawling URL: {url}")
            await self.page.goto(url, wait_until="networkidle")
            
            # Get the page content
            content = await self.page.content()
            soup = BeautifulSoup(content, 'html.parser')
            
            # Check if it's a product page by looking for og:type meta tag
            og_type = soup.find('meta', property='og:type')
            
            # Also check for structured data that indicates a product
            ld_json = soup.find('script', type='application/ld+json')
            is_product_page = False
            
            if og_type and og_type.get('content') == 'product':
                is_product_page = True
            elif ld_json:
                try:
                    ld_data = json.loads(ld_json.string)
                    if ld_data.get('@type') == 'Product':
                        is_product_page = True
                except (json.JSONDecodeError, AttributeError):
                    pass
            
            if not is_product_page:
                logging.info(f"Not a product page: {url}")
                return None
            
            # Extract product information
            product_data = self.extract_product_data(soup)
            product_data['product_url'] = url
            
            # Format data for WooCommerce
            woo_product = self.format_for_woocommerce(product_data)
            
            logging.info(f"Successfully extracted product data: {woo_product['name']}")
            return woo_product
            
        except Exception as e:
            logging.error(f"Error crawling {url}: {str(e)}")
            return None
    
    def extract_product_data(self, soup):
        """Extract product data from the BeautifulSoup object"""
        product_data = {
            'product_id': None,
            'product_name': None,
            'product_price': None,
            'product_old_price': None,
            'brand': None,
            'product_image_url': None,
            'category': None,
            'description': None,
            'sku': None
        }
        
        # Try to extract from structured data first (most reliable)
        ld_json = soup.find('script', type='application/ld+json')
        if ld_json:
            try:
                ld_data = json.loads(ld_json.string)
                if ld_data.get('@type') == 'Product':
                    product_data['product_name'] = ld_data.get('name')
                    product_data['product_id'] = ld_data.get('productID')
                    product_data['product_image_url'] = ld_data.get('image')
                    product_data['description'] = ld_data.get('description')
                    product_data['sku'] = ld_data.get('sku') or ld_data.get('productID')
                    
                    # Extract brand
                    brand = ld_data.get('brand')
                    if brand and isinstance(brand, dict):
                        product_data['brand'] = brand.get('name')
                    
                    # Extract price
                    offers = ld_data.get('offers')
                    if offers and isinstance(offers, dict):
                        product_data['product_price'] = offers.get('price')
                        product_data['currency'] = offers.get('priceCurrency')
            except (json.JSONDecodeError, AttributeError) as e:
                logging.warning(f"Error parsing JSON-LD: {str(e)}")
        
        # Extract product ID if not found in JSON-LD
        if not product_data['product_id']:
            product_id_meta = soup.find('meta', {'name': 'product_id'})
            if product_id_meta:
                product_data['product_id'] = product_id_meta.get('content')
            else:
                # Try to find it in a hidden input field
                product_id_input = soup.find('input', {'name': 'product_id'})
                if product_id_input:
                    product_data['product_id'] = product_id_input.get('value')
        
        # Use product ID as SKU if not found
        if not product_data['sku'] and product_data['product_id']:
            product_data['sku'] = product_data['product_id']
        
        # Extract product name if not found in JSON-LD
        if not product_data['product_name']:
            h1 = soup.find('h1', {'itemprop': 'name'})
            if h1:
                product_data['product_name'] = h1.text.strip()
        
        # Extract price if not found in JSON-LD
        if not product_data['product_price']:
            # Try meta tags first
            price_meta = soup.find('meta', {'name': 'product_price'})
            if price_meta:
                product_data['product_price'] = price_meta.get('content')
            
            # Try to find price in spans
            price_span = soup.find('span', {'itemprop': 'price'})
            if price_span:
                product_data['product_price'] = price_span.text.strip()
        
        # Extract old price / original price
        old_price_meta = soup.find('meta', {'name': 'product_old_price'})
        if old_price_meta:
            product_data['product_old_price'] = old_price_meta.get('content')
        
        # If old price equals current price, set to None
        if product_data['product_old_price'] == product_data['product_price']:
            product_data['product_old_price'] = None
        
        # Look for discounted price elements
        discounted_price = soup.find('div', {'class': 'km-price km-discounted'})
        if discounted_price:
            price_value = discounted_price.find('span', {'class': 'km-value'})
            if price_value and not product_data['product_old_price']:
                product_data['product_old_price'] = price_value.text.strip()
        
        # Extract brand if not found in JSON-LD
        if not product_data['brand']:
            brand_meta = soup.find('meta', {'name': 'product_brand'})
            if brand_meta:
                product_data['brand'] = brand_meta.get('content')
        
        # Extract product image if not found in JSON-LD
        if not product_data['product_image_url']:
            img = soup.find('img', {'itemprop': 'image'})
            if img:
                product_data['product_image_url'] = img.get('src')
        
        # Extract description if not found in JSON-LD
        if not product_data['description']:
            desc_div = soup.find('div', {'class': 'km-product-description'})
            if desc_div:
                product_data['description'] = desc_div.text.strip()
        
        # Extract category hierarchy from breadcrumbs
        breadcrumbs = soup.find('ul', {'itemtype': 'http://schema.org/BreadcrumbList'})
        if breadcrumbs:
            category_items = breadcrumbs.find_all('li', {'itemprop': 'itemListElement'})
            categories = []
            
            for item in category_items:
                name_span = item.find('span', {'itemprop': 'name'})
                if name_span:
                    category_name = name_span.text.strip()
                    if category_name:
                        categories.append(category_name)
                
                # Also check for the current item which might not have a span
                strong = item.find('strong', {'itemprop': 'name'})
                if strong:
                    category_name = strong.text.strip()
                    if category_name:
                        categories.append(category_name)
            
            if categories:
                product_data['category'] = categories
        
        return product_data
    
    def format_for_woocommerce(self, product_data):
        """Format the extracted data to be WooCommerce-friendly"""
        # Format price - remove currency symbol and commas, convert to float
        price = product_data['product_price']
        regular_price = None
        sale_price = None
        
        if price:
            # Remove currency symbols and non-numeric characters except decimal point
            price_str = re.sub(r'[^\d.]', '', str(price).replace(',', ''))
            try:
                regular_price = float(price_str)
            except ValueError:
                regular_price = None
        
        # Format old price if available
        old_price = product_data['product_old_price']
        if old_price:
            old_price_str = re.sub(r'[^\d.]', '', str(old_price).replace(',', ''))
            try:
                old_price_value = float(old_price_str)
                # In WooCommerce, if old_price > current_price, then old_price is regular_price and current_price is sale_price
                if old_price_value > regular_price:
                    sale_price = regular_price
                    regular_price = old_price_value
            except (ValueError, TypeError):
                pass
        
        # Format categories for WooCommerce
        categories = []
        if product_data['category']:
            if isinstance(product_data['category'], list):
                categories = product_data['category']
            else:
                # Split by '>' if it's a string
                categories = [cat.strip() for cat in product_data['category'].split('>')]
        
        # Create WooCommerce-friendly product object
        woo_product = {
            'ID': product_data['product_id'],
            'sku': product_data['sku'] or product_data['product_id'],
            'name': product_data['product_name'],
            'regular_price': regular_price,
            'sale_price': sale_price,
            'description': product_data['description'],
            'short_description': '',
            'categories': categories,
            'images': [{'src': product_data['product_image_url']}] if product_data['product_image_url'] else [],
            'tags': [],
            'attributes': [],
            'product_url': product_data['product_url'],
            'brand': product_data['brand']
        }
        
        # Add brand as attribute if available
        if product_data['brand']:
            woo_product['attributes'].append({
                'name': 'Brand',
                'options': [product_data['brand']],
                'visible': True
            })
        
        return woo_product

def get_urls_from_file(file_path):
    """Read URLs from a file, one URL per line"""
    with open(file_path, 'r', encoding='utf-8') as f:
        urls = [line.strip() for line in f if line.strip() and not line.strip().startswith('#')]
    return urls

async def main():
    # Set up argument parser
    parser = argparse.ArgumentParser(description='Crawl product information from e-commerce websites')
    parser.add_argument('--url', help='URL to crawl')
    parser.add_argument('--file', help='File containing URLs to crawl, one per line')
    parser.add_argument('--output', default='product_data.json', help='Output JSON file path')
    parser.add_argument('--format', choices=['json', 'csv'], default='json', help='Output format (json or csv)')
    args = parser.parse_args()
    
    # Get URLs to crawl
    urls = []
    if args.url:
        urls.append(args.url)
    elif args.file:
        if os.path.exists(args.file):
            urls = get_urls_from_file(args.file)
        else:
            logging.error(f"File not found: {args.file}")
            return
    else:
        # Default URL for testing
        urls = ["https://artisankala.com/%D9%84%D9%85%D9%8A%D9%86%D8%AA-cs7"]
        logging.info("No URL or file specified, using default test URL")
    
    if not urls:
        logging.error("No URLs to crawl")
        return
    
    # Initialize crawler
    crawler = ProductCrawler()
    await crawler.initialize()
    
    # Crawl URLs
    results = []
    for url in urls:
        product_data = await crawler.crawl_url(url)
        if product_data:
            results.append(product_data)
    
    # Save results to a file
    if args.format == 'json':
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
    elif args.format == 'csv':
        import csv
        csv_file = args.output if args.output.endswith('.csv') else args.output.replace('.json', '.csv')
        
        if results:
            # Get all possible fields from all products
            fieldnames = set()
            for product in results:
                fieldnames.update(product.keys())
            
            with open(csv_file, 'w', encoding='utf-8', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=sorted(fieldnames))
                writer.writeheader()
                for product in results:
                    # Handle nested structures for CSV
                    flat_product = {}
                    for key, value in product.items():
                        if isinstance(value, list) and key == 'categories':
                            flat_product[key] = '|'.join(value)
                        elif isinstance(value, list) and key == 'images':
                            if value:
                                flat_product[key] = value[0].get('src', '')
                            else:
                                flat_product[key] = ''
                        elif isinstance(value, list) and key == 'attributes':
                            # Skip attributes for CSV
                            pass
                        else:
                            flat_product[key] = value
                    writer.writerow(flat_product)
    
    await crawler.close()
    logging.info(f"Crawling completed. Extracted {len(results)} products.")

if __name__ == "__main__":
    asyncio.run(main()) 