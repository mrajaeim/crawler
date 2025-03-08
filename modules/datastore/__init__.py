from .product_repository import ProductRepository
from .image_repository import ImageRepository
from .failed_crawl_repository import FailedCrawlRepository

db_path = "./data/crawler.db"

product_repo = ProductRepository(db_path)
image_repo = ImageRepository(db_path)
failed_crawl_repo = FailedCrawlRepository(db_path)
