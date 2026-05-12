# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
import sys
import os
import hashlib
import random
from scrapy.exceptions import DropItem
from itemadapter import ItemAdapter

# Add project root to sys.path to import modules
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", ".."))
if project_root not in sys.path:
    sys.path.append(project_root)

from src.acquisition.bronze_publisher import BronzePublisher
from src.common.logger import get_logger

logger = get_logger("kafka_pipeline")

class KafkaPublishPipeline:
    def __init__(self):
        self.publisher = None

    def open_spider(self, spider):
        # Initialize publisher when spider opens
        self.publisher = BronzePublisher()
        logger.info(f"Initialized Kafka publisher for spider {spider.name}")

    def close_spider(self, spider):
        # Close publisher when spider closes
        if self.publisher:
            self.publisher.close()
            logger.info(f"Closed Kafka publisher for spider {spider.name}")
    
    def generate_article_id(self, url, title, source, content):
        """Generate a deterministic MD5 hash for article_id based on priority."""
        if url:
            id_input = url
        elif title or source:
            id_input = f"{title or ''}{source or ''}"
        else:
            id_input = content or str(random.random())
            
        return hashlib.md5(id_input.encode('utf-8')).hexdigest()

    def process_item(self, item, spider):
        adapter = ItemAdapter(item)
        
        # Check for null values in required fields
        required_fields = ['title', 'content', 'url', 'published_at', 'author']
        missing_or_null = []
        for field in required_fields:
            val = adapter.get(field)
            if val is None or str(val).strip() == "":
                missing_or_null.append(field)
                
        if missing_or_null:
            error_msg = f"Missing required fields: {', '.join(missing_or_null)} in URL: {adapter.get('url')}"
            logger.warning(error_msg)
            raise DropItem(error_msg)

        # Generate deterministic article_id
        article_id = self.generate_article_id(
            adapter.get('url'),
            adapter.get('title'),
            adapter.get('source'),
            adapter.get('content')
        )
        adapter['article_id'] = article_id
            
        # Convert item to dict and publish
        item_dict = adapter.asdict()
        success = self.publisher.publish_article(item_dict)
        
        if not success:
            logger.error(f"Failed to publish item to Kafka: {adapter.get('url')}")
            
        return item

