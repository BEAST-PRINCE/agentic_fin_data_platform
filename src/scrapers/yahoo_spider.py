import scrapy
import json
import logging
from bs4 import BeautifulSoup

class YahooSpider(scrapy.Spider):
    name = "yahoo_finance"
    
    custom_settings = {
        'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'ROBOTSTXT_OBEY': False
    }

    # Optional override from kwargs
    start_urls = []

    def __init__(self, *args, **kwargs):
        super(YahooSpider, self).__init__(*args, **kwargs)
        # If passed via command line e.g. -a url="http..."
        url = kwargs.get('url')
        if url:
            self.start_urls = [url]
            
    def parse(self, response):
        # We need to extract the JSON-LD schema containing NewsArticle
        schema_text = None
        for script in response.css('script[type="application/ld+json"]::text').getall():
            if '"@type":"NewsArticle"' in script or '"@type": "NewsArticle"' in script:
                schema_text = script
                break

        if not schema_text:
            self.logger.error(f"No NewsArticle JSON-LD found in {response.url}")
            return

        try:
            schema_data = json.loads(schema_text)
        except json.JSONDecodeError:
            self.logger.error(f"Failed to parse JSON-LD in {response.url}")
            return

        # Extract basic metadata
        title = schema_data.get('headline', '')
        description = schema_data.get('description', '')
        url = schema_data.get('mainEntityOfPage', response.url)
        published_at = schema_data.get('datePublished', '')
        
        # Author parsing
        author_data = schema_data.get('author', {})
        if isinstance(author_data, list) and len(author_data) > 0:
            author = author_data[0].get('name', '')
        elif isinstance(author_data, dict):
            author = author_data.get('name', '')
        else:
            author = str(author_data)

        # Source provider
        provider_data = schema_data.get('provider', {})
        source = provider_data.get('name', 'Yahoo Finance')
        
        # Category
        category = schema_data.get('articleSection', 'Finance')
        tags = schema_data.get('keywords', [])

        # Extract actual article body
        # For Yahoo Finance, the article body could be in several places
        selectors_to_try = [
            'div.caas-body',
            'div.article-body',
            'article',
            'div[class*="body"]',
            'main'
        ]
        
        body_html = None
        for selector in selectors_to_try:
            body_html = response.css(selector).get()
            if body_html:
                break
                
        content = ""
        if body_html:
            soup = BeautifulSoup(body_html, 'html.parser')
            # remove scripts and styles
            for script in soup(["script", "style"]):
                script.extract()
            content = soup.get_text(separator='\n', strip=True)
        
        if not content:
            # Fallback to just grabbing all paragraphs
            paragraphs = response.css('p::text').getall()
            content = '\n'.join([p.strip() for p in paragraphs if p.strip()])
            
        if not content:
            self.logger.warning(f"Could not find article body for {response.url}")

        article_item = {
            "title": title,
            "content": content,
            "description": description,
            "source": source,
            "url": url,
            "published_at": published_at,
            "author": author,
            "category": category,
            "tags": tags
        }

        yield article_item
