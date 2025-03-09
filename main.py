import json
import logging
from product_crawler import ProductCrawler
from modules.crawler_engine import CrawlerEngine

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
    urls = []
    with open('sitemap.json') as f:
        urls = json.load(f)
    
    if urls:
        # Create product crawler instance
        product_crawler = ProductCrawler()
        
        # Create and configure crawler engine
        engine = CrawlerEngine(
            crawler_service=product_crawler,
            delay_seconds=0.5,  # Configurable delay between requests
            max_urls=100,       # Maximum number of URLs to crawl
            stop_on_error=False # Whether to stop on first error
        )
        
        # Run crawling process
        stats = engine.crawl_urls(urls)
        
        # Print summary
        print("\nCrawling completed!")
        print(f"Processed {stats['total_urls']} URLs")
        print(f"Success: {stats['successful_crawls']}, Failed: {stats['failed_crawls']}, Skipped: {stats['skipped_urls']}")

if __name__ == "__main__":
    main()