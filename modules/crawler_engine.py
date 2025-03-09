import time
import logging
from typing import List
from .crawler_interface import CrawlerInterface


class CrawlerEngine:
    """
    Engine to manage crawling processes with different crawler services.
    Controls URL iteration, delays, statistics, and limits.
    """
    
    def __init__(
        self, 
        crawler_service: CrawlerInterface,
        delay_seconds: float = 0.5,
        max_urls: int = 100,
        stop_on_error: bool = False
    ):
        """
        Initialize the crawler engine
        
        Args:
            crawler_service: The crawler service implementing CrawlerInterface
            delay_seconds: Delay between requests in seconds
            max_urls: Maximum number of URLs to crawl
            stop_on_error: Whether to stop crawling on error
        """
        self.crawler_service = crawler_service
        self.delay_seconds = delay_seconds
        self.max_urls = max_urls
        self.stop_on_error = stop_on_error
        
        # Stats tracking
        self.stats = {
            "total_urls": 0,
            "successful_crawls": 0,
            "failed_crawls": 0,
            "skipped_urls": 0,
            "start_time": None,
            "end_time": None,
            "crawled_urls": [],
            "failed_urls": []
        }
    
    def initialize(self) -> None:
        """Initialize the crawler service"""
        self.crawler_service.initialize()
        logging.info(f"Crawler engine initialized with {self.crawler_service.__class__.__name__}")
        logging.info(f"Settings: delay={self.delay_seconds}s, max_urls={self.max_urls}")
    
    def close(self) -> None:
        """Close the crawler service and clean up resources"""
        self.crawler_service.close()
        logging.info("Crawler engine closed")
    
    def crawl_urls(self, urls: List[str]) -> dict:
        """
        Crawl a list of URLs using the provided crawler service
        
        Args:
            urls: List of URLs to crawl
            
        Returns:
            Dictionary containing crawling statistics
        """
        self.stats["start_time"] = time.time()
        self.stats["total_urls"] = len(urls)
        
        try:
            self.initialize()
            
            # Limit number of URLs to crawl
            urls_to_crawl = urls[:self.max_urls]
            if len(urls) > self.max_urls:
                logging.info(f"Limiting crawl to first {self.max_urls} URLs out of {len(urls)}")
            
            for url in urls_to_crawl:
                if self.crawler_service.not_crawled_before(url):
                    # Crawl the URL
                    result = self.crawler_service.crawl_url(url)
                    
                    if result is not None:
                        self.stats["successful_crawls"] += 1
                        self.stats["crawled_urls"].append(url)
                        logging.info(f"Successfully crawled URL: {url}")
                    else:
                        self.stats["failed_crawls"] += 1
                        self.stats["failed_urls"].append(url)
                        logging.warning(f"Failed to crawl URL: {url}")
                        
                        if self.stop_on_error:
                            logging.warning("Stopping crawl due to error (stop_on_error=True)")
                            break
                else:
                    self.stats["skipped_urls"] += 1
                    logging.info(f"Skipping already crawled URL: {url}")
                
                # Apply delay between requests
                time.sleep(self.delay_seconds)
                
        except Exception as e:
            logging.error(f"Error during crawl: {str(e)}")
            self.stats["failed_crawls"] += 1
        finally:
            self.close()
            self.stats["end_time"] = time.time()
            
            # Calculate total runtime
            runtime = self.stats["end_time"] - self.stats["start_time"]
            self.stats["runtime_seconds"] = runtime
            
            self._log_summary()
            
        return self.stats
    
    def _log_summary(self) -> None:
        """Log crawling statistics summary"""
        logging.info("=== Crawling Summary ===")
        logging.info(f"Total URLs: {self.stats['total_urls']}")
        logging.info(f"Successful crawls: {self.stats['successful_crawls']}")
        logging.info(f"Failed crawls: {self.stats['failed_crawls']}")
        logging.info(f"Skipped URLs: {self.stats['skipped_urls']}")
        
        runtime = self.stats.get("runtime_seconds", 0)
        runtime_mins = int(runtime // 60)
        runtime_secs = int(runtime % 60)
        logging.info(f"Total runtime: {runtime_mins}m {runtime_secs}s")
