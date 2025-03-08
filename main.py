import logging
from product_crawler import crawl_urls

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("crawler.log"),
        logging.StreamHandler()
    ]
)

def main():
    """Main entry point for the crawler application"""
    urls = [
        "https://artisankala.com/%D9%84%D9%85%D9%8A%D9%86%D8%AA-cs7"
    ]
    if urls:
        crawl_urls(urls)

if __name__ == "__main__":
    main()