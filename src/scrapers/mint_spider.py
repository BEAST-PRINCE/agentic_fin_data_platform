import asyncio
import json
import logging
import sys
import os
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup

# Ensure src modules can be imported if needed later
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

async def scrape_mint(url: str):
    """
    Scrape a Mint page using Playwright.
    Extracts structured data from application/ld+json and maps to the common schema.
    """
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        
        try:
            logger.info(f"Navigating to {url}...")
            await page.goto(url, wait_until="commit", timeout=30000)
            
            # Wait a bit for JS to populate JSON-LD
            await page.wait_for_timeout(2000)
            
            # Extract JSON-LD scripts
            json_ld_scripts = await page.locator('script[type="application/ld+json"]').all_text_contents()
            
            schema_data = None
            for script in json_ld_scripts:
                try:
                    data = json.loads(script, strict=False)
                    # Handle both dict and list types of JSON-LD
                    if isinstance(data, list):
                        for item in data:
                            if item.get('@type') == 'NewsArticle' or item.get('@type') == 'Article':
                                schema_data = item
                                break
                    elif isinstance(data, dict):
                        if data.get('@type') == 'NewsArticle' or data.get('@type') == 'Article':
                            schema_data = data
                            break
                        elif '@graph' in data:
                            for item in data['@graph']:
                                if item.get('@type') == 'NewsArticle' or item.get('@type') == 'Article':
                                    schema_data = item
                                    break
                except json.JSONDecodeError:
                    continue
                
                if schema_data:
                    break
            
            if not schema_data:
                logger.warning(f"No NewsArticle JSON-LD found in {url}. Will try HTML extraction.")
                schema_data = {}

            # Map fields
            title = schema_data.get('headline', '')
            description = schema_data.get('description', '')
            source = "Mint"

            # Parse Author
            author_data = schema_data.get('author', {})
            if isinstance(author_data, list) and len(author_data) > 0:
                author = author_data[0].get('name', '')
            elif isinstance(author_data, dict):
                author = author_data.get('name', '')
            else:
                author = str(author_data)

            # Dates and Category
            published_at = schema_data.get('datePublished', '')
            category = schema_data.get('articleSection', '')
            tags = schema_data.get('keywords', [])
            
            # If tags is a comma-separated string
            if isinstance(tags, str):
                tags = [t.strip() for t in tags.split(',') if t.strip()]

            # Extract body
            content = schema_data.get('articleBody', '')
            
            # If no articleBody, fallback to Playwright DOM extraction
            if not content:
                logger.info("Extracting content from HTML fallback...")
                selectors = ['div.content_wrapper', 'div.paywall', 'article', 'div[class*="content"]']
                for selector in selectors:
                    try:
                        element = await page.locator(selector).first
                        if await element.count() > 0:
                            html_content = await element.inner_html()
                            soup = BeautifulSoup(html_content, 'html.parser')
                            for s in soup(["script", "style"]):
                                s.extract()
                            content = soup.get_text(separator='\n', strip=True)
                            if content:
                                break
                    except Exception:
                        pass
                        
            # If still no content, get paragraphs
            if not content:
                paragraphs = await page.locator('p').all_inner_texts()
                content = '\n'.join([p.strip() for p in paragraphs if p.strip()])
            
            # If no title from schema, get from title tag
            if not title:
                title = await page.title()

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
            
            return article_item

        except Exception as e:
            logger.error(f"Error scraping {url}: {e}")
            return None
        finally:
            await browser.close()

if __name__ == "__main__":
    if len(sys.argv) > 1:
        url = sys.argv[1]
        result = asyncio.run(scrape_mint(url))
        print(json.dumps(result, indent=2))
    else:
        print("Please provide a Mint URL to scrape.")
