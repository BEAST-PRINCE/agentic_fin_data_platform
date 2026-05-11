import scrapy
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule
from datetime import datetime, timezone
import sys
import os

# Add the project root to sys.path to import central modules
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", ".."))
if project_root not in sys.path:
    sys.path.append(project_root)

from src.common.logger import get_logger

# Initialize central logger
logger = get_logger("moneycontrol_business_spider")



class MoneycontrolBusinessSpider(CrawlSpider):
    name = "moneycontrol_business"
    allowed_domains = ["www.moneycontrol.com"]
    start_urls = ["https://www.moneycontrol.com/news/business/markets/"]

    custom_settings = {
        "USER_AGENT": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/136.0.0.0 Safari/537.36"
        ),
        "DEPTH_LIMIT": 3,
    }

    rules = (
        Rule(LinkExtractor(
                allow=(r"/news/business/.*\.html$"),
                # deny=(r"/tag/", r"/author/", r"/page/", r"/ipo/"),
                unique=True,
            ),
            callback="parse_article",
            follow=True
        ),
    )

    def parse_article(self, response):
        logger.info(f"Parsing article: {response.url}")
        title = response.xpath('//h1[contains(@class, "article_title")]/text()').get(default="").strip()
        description = response.xpath('//div[contains(@class, "article_desc")]/text()').get(default="").strip()
        paragraphs = response.xpath('//div[contains(@class, "content_wrapper")]//p//text()').getall()
        content = " ".join(p.strip()for p in paragraphs if p.strip())
        author = response.xpath('//div[contains(@class, "article_author")]//a/text()').get(default="").strip()
        published_date = response.xpath('//div[contains(@class, "article_schedule")]//span/text()').get(default="").strip()
        published_time = response.xpath('normalize-space(//div[contains(@class, "article_schedule")])').get(default="")
        published_at = f"{published_date} {published_time}".strip()
        category = response.xpath('//div[contains(@class, "article_consum_wrapper")]/@data-cat').get(default="business")
        tags = response.xpath('//meta[@name="news_keywords"]/@content').get()

        if tags:
            tags = [tag.strip() for tag in tags.split(",") if tag.strip()]
        else:
            tags = []

        article = {
            "title": title,
            "content": content,
            "description": description,
            "source": "Moneycontrol",
            "url": response.url,
            "published_at": published_at,
            "author": author,
            "category": category,
            "ingested_at": datetime.utcnow().isoformat(),
            "tags": tags,
        }
        logger.info(f"Successfully scraped article from: {response.url}")
        yield article