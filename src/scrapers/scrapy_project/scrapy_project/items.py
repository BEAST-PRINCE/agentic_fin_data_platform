# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class ScrapyProjectItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    pass

class NewsArticle(scrapy.Item):
    title = scrapy.Field()
    content = scrapy.Field()
    description = scrapy.Field()
    source = scrapy.Field()
    url = scrapy.Field()
    published_at = scrapy.Field()
    author = scrapy.Field()
    category = scrapy.Field()
    ingested_at = scrapy.Field()
    tags = scrapy.Field()
