# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html

import sys
import os
from scrapy.exceptions import DropItem
from itemadapter import ItemAdapter

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", ".."))
if project_root not in sys.path:
    sys.path.append(project_root)

from src.ingestion.kafka.bronze_publisher import BronzePublisher
from src.ingestion.kafka.schema import generate_article_id
from src.common.logger import get_logger

logger = get_logger("kafka_pipeline")


class KafkaPublishPipeline:
    def __init__(self):
        self.publisher = None

    def open_spider(self, spider):
        self.publisher = BronzePublisher()
        logger.info(f"Initialized Kafka publisher for spider {spider.name}")

    def close_spider(self, spider):
        if self.publisher:
            self.publisher.close()
            logger.info(f"Closed Kafka publisher for spider {spider.name}")

    def process_item(self, item, spider):
        adapter = ItemAdapter(item)

        if not adapter.get("author") or str(adapter.get("author")).strip() == "":
            adapter["author"] = "unknown"

        required_fields = ["title", "content", "url"]
        missing_or_null = []
        for field in required_fields:
            val = adapter.get(field)
            if val is None or str(val).strip() == "":
                missing_or_null.append(field)

        if missing_or_null:
            error_msg = (
                f"Missing required fields: {', '.join(missing_or_null)} "
                f"in URL: {adapter.get('url')}"
            )
            logger.warning(error_msg)
            raise DropItem(error_msg)

        adapter["article_id"] = generate_article_id(
            url=adapter.get("url"),
            title=adapter.get("title"),
            source=adapter.get("source"),
            content=adapter.get("content"),
        )

        item_dict = adapter.asdict()
        success = self.publisher.publish_article(item_dict)

        if not success:
            logger.error(f"Failed to publish item to Kafka: {adapter.get('url')}")

        return item
