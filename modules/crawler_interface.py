from abc import ABC, abstractmethod
from bs4 import BeautifulSoup
from typing import Dict, Any, Optional, Union


class CrawlerInterface(ABC):
    """
    Interface for crawler services to be used with the Crawler engine.
    All crawler services must implement these methods.
    """
    
    @abstractmethod
    def initialize(self) -> None:
        """Initialize the crawler (e.g., start browser, set up resources)"""
        pass
    
    @abstractmethod
    def close(self) -> None:
        """Close and clean up resources"""
        pass
    
    @abstractmethod
    def not_crawled_before(self, url: str, url_type: str = "product") -> bool:
        """Check if the URL has been crawled before"""
        pass
    
    @abstractmethod
    def crawl_url(self, url: str) -> Optional[Union[str, int]]:
        """
        Crawl a specific URL and process its content
        
        Args:
            url: The URL to crawl
            
        Returns:
            Optional ID of the processed item or None if crawling failed
        """
        pass
    
    @abstractmethod
    def extract_product_data(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """
        Extract data from the soup object
        
        Args:
            soup: BeautifulSoup object containing the page content
            
        Returns:
            Dictionary with extracted data
        """
        pass
