import scrapy
from datetime import datetime, timezone
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule
from scrapy_project.items import NewsArticle
import sys
import os

# Add the project root to sys.path to import central modules
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", ".."))
if project_root not in sys.path:
    sys.path.append(project_root)

from src.common.logger import get_logger

# Initialize central logger
logger = get_logger("financialexpress_markets_spider")


class FinancialexpressMarketsSpider(CrawlSpider):
    name = "financialexpress_markets"
    allowed_domains = ["financialexpress.com"]
    start_urls = ["https://www.financialexpress.com/"]

    custom_settings = {
        "USER_AGENT": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/136.0.0.0 Safari/537.36"
        ),
    }

    rules = (
        Rule(LinkExtractor(
                # allow=(r"/market/.*\.html$", r"/business/.*\.html$",),
                allow=(r"/market/.*", r"/business/.*"),
                deny=(r"/tag/", r"/author/", r"/page/", r"/ipo/"),
                unique=True,
            ),
            callback="parse_article",
            follow=False
        ),
    )

    def parse_article(self, response):
        logger.info(f"Parsing article: {response.url}")
        title = response.xpath("//h1/text()").get(default="").strip()
        description = response.xpath("//h2/text()").get(default="").strip()
        paragraphs = response.xpath('//div[contains(@class, "post-content")]//p//text()').getall()
        content = " ".join(p.strip() for p in paragraphs if p.strip())
        author = response.xpath('//span[@id="author-link"]//a/text()').get(default="").strip()
        published_at = response.xpath('//time/@datetime').get(default="").strip()
        category = response.xpath('//ol[contains(@class, "breadcrumb")]//li[2]//a/text()').get(default="").strip()
        tags = response.xpath('//div[contains(@class, "ctd_viewmoretags")]//a/text()').getall()
        tags = [tag.strip() for tag in tags if tag.strip()]

        article = NewsArticle(
            title=title,
            content=content,
            description=description,
            source="Financial Express",
            url=response.url,
            published_at=published_at,
            author=author,
            category=category,
            ingested_at=datetime.now(timezone.utc).isoformat(),
            tags=tags,
        )
        logger.info(f"Successfully scraped article from: {response.url}")
        yield article