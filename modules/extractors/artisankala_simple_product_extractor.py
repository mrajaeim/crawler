import json
import logging
from bs4 import BeautifulSoup
from modules.utils.safely_parse_json_string import normalize_json_string

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("ArtisankalaSimpleProductExtractor.log", encoding='utf-8'),
        logging.StreamHandler()
    ]
)

class ArtisankalaSimpleProductExtractor:
    @staticmethod
    def extract(soup: BeautifulSoup):
        """Main method to extract all product data from the HTML."""
        product_data = {
            'product_id': None,
            'product_name': None,
            'product_price': None,
            'product_old_price': None,
            'brand': None,
            'product_image_url': None,
            'category': None,
            'description': None,
            'sku': None,
            'has_variations': False,
            'variations': [],
            'product_gallery_images': []
        }

        # Extract data from structured data (JSON-LD)
        ArtisankalaSimpleProductExtractor._extract_from_json_ld(soup, product_data)
        
        # Extract basic product information
        ArtisankalaSimpleProductExtractor._extract_basic_info(soup, product_data)

        # Extract product variations
        ArtisankalaSimpleProductExtractor._extract_variations(soup, product_data)

        # Extract product images and gallery
        ArtisankalaSimpleProductExtractor._extract_images(soup, product_data)

        # Extract product description
        ArtisankalaSimpleProductExtractor._extract_description(soup, product_data)

        # Extract category information
        ArtisankalaSimpleProductExtractor._extract_categories(soup, product_data)

        return product_data

    @staticmethod
    def _extract_from_json_ld(soup: BeautifulSoup, product_data: dict):
        """Extract product data from JSON-LD structured data."""
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

                    # Extract price from offers (commented out in original code)
                    # offers = ld_data.get('offers')
                    # if offers and isinstance(offers, dict):
                    #     product_data['product_price'] = offers.get('price')
            except (json.JSONDecodeError, AttributeError) as e:
                logging.warning(f"Error parsing JSON-LD: {str(e)}")

    @staticmethod
    def _extract_basic_info(soup: BeautifulSoup, product_data: dict):
        """Extract basic product information like name, price, brand."""
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

    @staticmethod
    def _extract_images(soup: BeautifulSoup, product_data: dict):
        """Extract product images and gallery."""
        # Extract main product image if not found in JSON-LD
        if not product_data['product_image_url']:
            img = soup.find('img', {'itemprop': 'image'})
            if img:
                product_data['product_image_url'] = img.get('src')
                
        # Extract product gallery images
        # Look for the gallery container within div.km-product-right
        right_column = soup.find('div', {'class': 'km-product-right'})
        if right_column:
            gallery_container = right_column.find('div', {'class': 'km-product-gallery'})
            if gallery_container:
                # Find all gallery items in the lightSlider
                gallery_items = gallery_container.select('ul.km-gallery li.item')
                
                for item in gallery_items:
                    # Get the image URL from the data-src attribute or from the img tag
                    image_url = item.get('data-src')
                    
                    # If data-src is not available, try to get from the img tag
                    if not image_url:
                        img_tag = item.find('img', {'itemprop': 'image'})
                        if img_tag:
                            image_url = img_tag.get('src')
                    
                    if image_url and image_url not in product_data['product_gallery_images']:
                        product_data['product_gallery_images'].append(image_url)
                
                logging.info(f"Found {len(product_data['product_gallery_images'])} gallery images for product")
                
                # If we found gallery images but no main product image, use the first gallery image
                if product_data['product_gallery_images'] and not product_data['product_image_url']:
                    product_data['product_image_url'] = product_data['product_gallery_images'][0]

    @staticmethod
    def _extract_description(soup: BeautifulSoup, product_data: dict):
        """Extract product description."""
        if not product_data['description']:
            desc_div = soup.find('div', {'class': 'km-product-description'})
            if desc_div:
                product_data['description'] = desc_div.text.strip()

    @staticmethod
    def _extract_categories(soup: BeautifulSoup, product_data: dict):
        """Extract category hierarchy from breadcrumbs."""
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

    @staticmethod
    def _extract_variations(soup: BeautifulSoup, product_data: dict):
        """Extract product variations."""
        variations_container = soup.find('div', {'class': 'km--products_container'})
        if variations_container:
            product_data['has_variations'] = True
            
            # Extract variations
            variation_items = variations_container.find_all('span', {'class': 'km-item'})
            for item in variation_items:
                variation = {
                    'code': None,
                    'image_url': None,
                    'id': None
                }
                
                # Extract variation code
                code_span = item.find('span', {'class': 'km-title'})
                if code_span:
                    variation['code'] = code_span.text.strip()
                
                # Extract variation image
                img = item.find('img', {'class': 'km-img'})
                if img:
                    variation['image_url'] = img.get('src')
                
                # Extract variation ID
                variation['id'] = item.get('km-id')
                
                if variation['code'] and variation['image_url']:
                    product_data['variations'].append(variation)
            
            logging.info(f"Found {len(product_data['variations'])} variations for product")
