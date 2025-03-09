import os
import json
import logging

import requests
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
from urllib.parse import urlparse
from modules.datastore import product_repo, image_repo, failed_crawl_repo, variation_repo
from modules.utils import formatters
from modules.utils.incremental_id_generator import IncrementalIdGenerator
from modules.crawler_interface import CrawlerInterface

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("crawler.log", encoding='utf-8'),
        logging.StreamHandler()
    ]
)

# Create images directory if it doesn't exist
IMAGES_DIR = "data/images"
os.makedirs(IMAGES_DIR, exist_ok=True)


class ProductCrawler(CrawlerInterface):
    def __init__(self):
        self.browser = None
        self.context = None
        self.page = None
        self.untitled_image_id_generator = IncrementalIdGenerator()

    def initialize(self):
        """Initialize the Playwright browser"""
        playwright = sync_playwright().start()
        self.browser = playwright.chromium.launch(headless=True)
        self.context = self.browser.new_context()
        self.page = self.context.new_page()

    def close(self):
        """Close the browser and clean up resources"""
        if self.browser:
            self.browser.close()

    def not_crawled_before(self, url, url_type="product"):
        match url_type:
            case "image":
                return not image_repo.get_image_by_url(url)
            case "product":
                return not product_repo.get_product_by_url(url)
            case _:
                raise ValueError(f"Unsupported url type: {url_type}")

    def crawl_url(self, url):
        """Crawl a specific URL and extract product information"""
        try:
            logging.info(f"Crawling URL: {url}")
            self.page.goto(url, wait_until="networkidle")

            # Get the page content
            content = self.page.content()
            soup = BeautifulSoup(content, 'html.parser')

            # Check if it's a product page
            if not self._is_product_page(soup):
                logging.info(f"Not a product page: {url}")
                return None

            # Extract product information
            product_data = self.extract_product_data(soup)
            product_data['product_url'] = url

            # Save product to database
            return self._save_product_to_db(product_data)

        except Exception as e:
            logging.error(f"Error crawling {url}: {str(e)}")
            # Record the failure
            failed_crawl_repo.create_failed_crawl(
                url=url,
                type="product",
                error=str(e),
                foreign_id=None,
                status="failed"
            )
            return None

    def _is_product_page(self, soup):
        """Check if the page is a product page"""
        # Check for og:type meta tag
        og_type = soup.find('meta', property='og:type')
        if og_type and og_type.get('content') == 'product':
            return True

        # Check for structured data that indicates a product
        ld_json = soup.find('script', type='application/ld+json')
        if ld_json:
            try:
                ld_data = json.loads(ld_json.string)
                if ld_data.get('@type') == 'Product':
                    return True
            except (json.JSONDecodeError, AttributeError):
                pass

        return False

    def extract_product_data(self, soup: BeautifulSoup):
        """Extract product data from the BeautifulSoup object"""
        from modules.extractors.artisankala_simple_product_extractor import \
            ArtisankalaSimpleProductExtractor as ASPExtractor
        return ASPExtractor.extract(soup)

    def _save_product_to_db(self, product_data):
        """Save product data to the database"""
        try:
            current_price = formatters.format_price(product_data['product_price'])
            old_price = formatters.format_price(product_data['product_old_price']) if product_data[
                'product_old_price'] else None

            has_sales_price = current_price != old_price and old_price is not None
            price = current_price if not has_sales_price else old_price
            sales_price = current_price if has_sales_price else None

            # Check if product has variations
            has_variations = product_data.get('has_variations', False)

            # Create product in database
            product_id = product_repo.create_product(
                title=product_data['product_name'] or '',
                price=price,
                sales_price=sales_price,
                category=product_data['category'] or '',
                short_desc=product_data['description'] or '',
                brand=product_data['brand'] or '',
                url=product_data['product_url'],
                has_variations=has_variations
            )

            # Save product images
            # Check if we have multiple images in a gallery
            if 'product_gallery_images' in product_data and product_data['product_gallery_images']:
                # Save all gallery images
                for image_url in product_data['product_gallery_images']:
                    if image_url and self.not_crawled_before(image_url, url_type="image"):
                        self._save_image(product_id, image_url)
            # If no gallery images but we have a main image, save that
            elif product_data['product_image_url'] and self.not_crawled_before(product_data['product_image_url'], url_type="image"):
                self._save_image(product_id, product_data['product_image_url'])

            # Process variations if present
            if has_variations and product_data.get('variations'):
                self._process_variations(product_id, product_data['variations'])

            logging.info(f"Successfully saved product ID: {product_id}")
            return product_id

        except Exception as e:
            logging.error(f"Error saving product to database: {str(e)}")
            failed_crawl_repo.create_failed_crawl(
                url=product_data['product_url'],
                type="db_save",
                error=str(e),
                foreign_id=None,
                status="failed"
            )
            return None

    def _process_variations(self, parent_product_id, variations):
        """Process and save product variations"""
        logging.info(f"Processing {len(variations)} variations for product {parent_product_id}")

        for variation in variations:
            try:
                # Create variation record
                variation_id = variation_repo.create_variation(
                    product_id=parent_product_id,
                    variation_code=variation['code']
                )

                # Save variation image
                if variation['image_url'] and self.not_crawled_before(variation['image_url'], url_type="image"):
                    image_id = self._save_variation_image(
                        product_id=parent_product_id,
                        variation_id=variation_id,
                        image_url=variation['image_url']
                    )

                    # Update variation with image ID
                    if image_id:
                        variation_repo.update_variation(
                            variation_id=variation_id,
                            image_id=image_id
                        )

                logging.info(
                    f"Saved variation {variation['code']} (ID: {variation_id}) for product {parent_product_id}")

            except Exception as e:
                logging.error(f"Error saving variation {variation['code']} for product {parent_product_id}: {str(e)}")

    def _save_image(self, product_id, image_url):
        """Download and save image, then record in database"""
        try:
            # Generate filename from URL
            parsed_url = urlparse(image_url)
            filename = os.path.basename(parsed_url.path)
            if not filename:
                filename = f"product_{self.untitled_image_id_generator.get_id(product_id)}_image.jpg"

            # Create full path
            image_path = os.path.join(IMAGES_DIR, filename)

            # Download image
            response = requests.get(image_url, stream=True)
            if response.status_code == 200:
                with open(image_path, 'wb') as f:
                    for chunk in response.iter_content(1024):
                        f.write(chunk)

                # Save image record in database
                image_id = image_repo.create_image(product_id, image_url)
                logging.info(f"Saved image for product {product_id}: {image_path}")
                return image_id
            else:
                raise Exception(f"Failed to download image: HTTP {response.status_code}")

        except Exception as e:
            logging.error(f"Error saving image for product {product_id}: {str(e)}")
            failed_crawl_repo.create_failed_crawl(
                url=image_url,
                type="image",
                error=str(e),
                foreign_id=product_id,
                status="failed"
            )
            return None

    def _save_variation_image(self, product_id, variation_id, image_url):
        """Download and save variation image, then record in database"""
        try:
            # Generate filename from URL
            parsed_url = urlparse(image_url)
            filename = os.path.basename(parsed_url.path)
            if not filename:
                filename = f"variation_{variation_id}_image.jpg"

            # Create full path
            image_path = os.path.join(IMAGES_DIR, filename)

            # Download image
            response = requests.get(image_url, stream=True)
            if response.status_code == 200:
                with open(image_path, 'wb') as f:
                    for chunk in response.iter_content(1024):
                        f.write(chunk)

                # Save image record in database with variation type
                image_id = image_repo.create_image(
                    product_id=product_id,
                    image_url=image_url,
                    image_type='variation',
                    variation_id=variation_id
                )

                logging.info(f"Saved variation image for product {product_id}, variation {variation_id}: {image_path}")
                return image_id
            else:
                raise Exception(f"Failed to download variation image: HTTP {response.status_code}")

        except Exception as e:
            logging.error(f"Error saving variation image for product {product_id}, variation {variation_id}: {str(e)}")
            failed_crawl_repo.create_failed_crawl(
                url=image_url,
                type="variation_image",
                error=str(e),
                foreign_id=variation_id,
                status="failed"
            )
            return None
