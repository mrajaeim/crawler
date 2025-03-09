from .product_repository import ProductRepository
from .image_repository import ImageRepository
from .failed_crawl_repository import FailedCrawlRepository
from .variation_repository import VariationRepository

db_path = "./data/crawler.db"

product_repo = ProductRepository(db_path)
image_repo = ImageRepository(db_path)
failed_crawl_repo = FailedCrawlRepository(db_path)
variation_repo = VariationRepository("data/crawler.db")