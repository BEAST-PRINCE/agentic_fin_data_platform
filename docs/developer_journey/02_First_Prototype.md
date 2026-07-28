# 02 - The First Prototype

*Date: March 2026*

Once I decided I needed Big Data infrastructure, my first instinct was Hadoop. But after a few hours of trying to configure Hadoop clusters locally on a Windows machine, I quickly realized it was going to be an absolute nightmare for rapid prototyping.

I pivoted to Docker Compose. If I couldn't run Hadoop easily, I could at least run isolated containers for my databases and APIs. 

This led to my first major battle with infrastructure. I spent an embarrassing amount of time fighting with a `docker-compose.yml` file. Docker kept throwing a fatal error: `All mapping items must start at the same column`. It turned out to be a single bad indentation on line 27. It's funny how you can have grand visions of AI agents predicting the stock market, but you get completely blocked by two missing spaces in a YAML file.

Once Docker was running, I built the first real prototype. It wasn't a datalake yet. It was just a basic Python scraper pulling financial news and dumping raw JSON into a local folder. 

I wrote a simple script to read the JSON and pass it to an LLM. It "worked," but it was incredibly brittle. If the scraper pulled too many articles, the LLM ran out of memory. If it pulled too few, the LLM hallucinated facts. 

I realized I couldn't just feed raw web scrapes to an AI. I needed a real data engineering pipeline. And I definitely needed strict conversational boundaries—foreshadowing the massive "Session Isolation" bugs that would plague my multi-agent pipeline months later.

---
⬅️ **Previous:** [01 - The Idea](01_The_Idea.md) | **Next:** [03 - Data Engineering](03_Data_Engineering.md) ➡️
