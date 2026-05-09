import scrapy
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule


class MintCompaniesSpider(CrawlSpider):
    name = "mint_companies"

    allowed_domains = ["livemint.com"]

    start_urls = [
        "https://www.livemint.com/companies"
    ]

    custom_settings = {
        "USER_AGENT": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/136.0.0.0 Safari/537.36"
        ),
    }

    rules = (
        Rule(
            LinkExtractor(
                allow=r"/companies/.*\.html"
            ),
            callback="parse_article",
            follow=False
        ),
    )

    def parse_article(self, response):

        yield {
            "url": response.url,
            "title": response.xpath("//h1/text()").get(),
        }