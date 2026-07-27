# Scrapers (`src/scrapers/`)

## 🕸️ Why does this folder exist?

This folder is the starting point of the entire data lifecycle. My AI agents need fresh, relevant financial news and data to make intelligent decisions. Since I am building this platform completely locally without paying for expensive enterprise API subscriptions, I wrote these scrapers to go out into the wild and gather that data autonomously.

## 🕷️ Responsibilities & Internal Structure

The scripts in this folder are responsible for:
* **Targeting:** Navigating to specific financial news sites, RSS feeds, or public data portals.
* **Extraction:** Pulling out the relevant HTML elements (headlines, article bodies, timestamps, author names).
* **Initial Formatting:** Structuring the scraped data into basic Python dictionaries.
* **Handoff:** Passing the dictionaries over to the Kafka producers (located in `src/ingestion/`).

## 🔄 Data Flow

`External Websites / APIs` ➔ `Scraper Scripts` ➔ `Python Dicts` ➔ *(Handed off to `src/ingestion/`)*

## 🔌 Dependencies & Extension Points

* **Dependencies:** These scripts rely on libraries like `requests`, `BeautifulSoup`, or `Scrapy`, depending on the complexity of the target site.
* **Extension Points:** Want to add Yahoo Finance? Bloomberg? A new SEC filing parser? Drop a new scraper script in this folder, point it at the URL, map the HTML tags, and hook it up to the ingestion producer.

## 🐛 Debugging Tips

* **Websites Change UI:** This is the most brittle part of any data pipeline. If data suddenly stops flowing into Kafka, 99% of the time it is because the target website changed their CSS classes or HTML structure. Check the scraper logs for `AttributeError: 'NoneType' object has no attribute 'text'`.
* **Rate Limiting & IP Bans:** If the scraper is returning HTTP 403 or 429, the site is blocking us. Ensure respectful scraping: add `time.sleep()`, use rotating user agents, or reconsider the scraping frequency.
