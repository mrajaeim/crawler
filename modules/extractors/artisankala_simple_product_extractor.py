import json
import logging
from bs4 import BeautifulSoup
from modules.utils.safely_parse_json_string import normalize_json_string

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("ArtisankalaSimpleProductExtractor.log"),
        logging.StreamHandler()
    ]
)

class ArtisankalaSimpleProductExtractor:
    @staticmethod
    def extract(soup: BeautifulSoup):
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
                ld_data = normalize_json_string(ld_json.string)
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
                    # offers = ld_data.get('offers')
                    # if offers and isinstance(offers, dict):
                        # product_data['product_price'] = offers.get('price')
            except (json.JSONDecodeError, AttributeError) as e:
                logging.warning(f"Error parsing JSON-LD: {str(e)}")

        # Extract product name if not found in JSON-LD
        if not product_data['product_name']:
            h1 = soup.find('h1', {'itemprop': 'name'})
            if h1:
                product_data['product_name'] = h1.text.strip()

        # Extract price if not found in JSON-LD
        if not product_data['product_price']:
            price_span = soup.find('span', {'itemprop': 'price'})
            if price_span:
                product_data['product_price'] = price_span.text.strip()

        # Extract old price / original price
        old_price_meta = soup.find('meta', {'name': 'product_old_price'})
        if old_price_meta:
            product_data['product_old_price'] = old_price_meta.get('content')

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

            if categories:
                product_data['category'] = ' > '.join(categories)

        return product_data
