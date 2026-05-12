import scrapy
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule
from datetime import datetime, timezone
import json
import sys
import os
from scrapy_project.items import NewsArticle

# Add the project root to sys.path to import central modules
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", ".."))
if project_root not in sys.path:
    sys.path.append(project_root)

from src.common.logger import get_logger

# Initialize central logger
logger = get_logger("mint_cryptocurrencies_spider")


class MintCompaniesSpider(CrawlSpider):
    name = "mint_cryptocurrencies"
    allowed_domains = ["livemint.com"]
    start_urls = ["https://www.livemint.com/cryptocurrency"]

    custom_settings = {
        "USER_AGENT": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/136.0.0.0 Safari/537.36"
        ),
    }

    rules = (
        Rule(
            LinkExtractor(allow=r"/cryptocurrency/.*\.html"),
            callback="parse_article",
            follow=False
        ),
    )

    def parse_article(self, response):
        logger.info(f"Parsing article: {response.url}")
        json_ld_scripts = response.xpath(
            '//script[@type="application/ld+json"]/text()'
        ).getall()
        article_data = None
        for script in json_ld_scripts:
            try:
                data = json.loads(script.strip())
                # Sometimes JSON-LD is a LIST
                if isinstance(data, list):
                    for item in data:
                        if (
                            isinstance(item, dict)
                            and item.get("@type") == "NewsArticle"
                        ):
                            article_data = item
                            break
                # Sometimes JSON-LD is a DICT
                elif (
                    isinstance(data, dict)
                    and data.get("@type") == "NewsArticle"
                ):
                    article_data = data
                if article_data:
                    break
            except Exception as e:
                logger.warning(
                    f"JSON parse failed for script in {response.url}: {e}"
                )

        # FALLBACK HTML extraction
        if not article_data:
            logger.warning(
                f"No NewsArticle schema found in JSON-LD for {response.url}. Attempting fallback HTML extraction."
            )
            title = response.xpath("//h1/text()").get()
            content = " ".join(
                response.xpath(
                    '//div[contains(@class, "storyParagraph")]//p//text()'
                ).getall()
            )
            article = NewsArticle(
                title=title,
                content=content,
                description=None,
                source="LiveMint",
                url=response.url,
                published_at=None,
                author=None,
                category="companies",
                ingested_at=datetime.now(timezone.utc).isoformat(),
                tags=[],
            )
            logger.info(f"Successfully scraped article (fallback) from: {response.url}")
            yield article
            return

        article = NewsArticle(
            title=article_data.get("headline"),
            content=article_data.get("articleBody"),
            description=article_data.get("description"),
            source="LiveMint",
            url=article_data.get("url"),
            published_at=article_data.get("datePublished"),
            author=(
                article_data.get("author", {})
                .get("name")
                if isinstance(article_data.get("author"), dict)
                else article_data.get("author")
            ),
            category="companies",
            ingested_at=datetime.now(timezone.utc).isoformat(),
            tags=article_data.get("keywords", []),
        )
        logger.info(f"Successfully scraped article from: {response.url}")
        yield article