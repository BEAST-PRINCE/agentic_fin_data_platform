# 01 - The Idea (and the Messy Beginnings)

*Date: Early 2026*

Every overly-ambitious software project starts with a Jupyter Notebook that gets out of hand. 

This project was no different. 

In early 2026, I wasn't trying to build an "Agentic Datalake." I was just trying to build a cryptocurrency price predictor in a notebook called `data_creation.ipynb`. The goal was simple: scrape some practice data, run a basic model, and see if I could predict Bitcoin's next move.

I spent the first few days just trying to modularize that messy notebook. I split the logic into `data_utils.py`, `model_utils.py`, and `app.py`. It felt good. I had a clean little Python project. 

Then, I wanted to scale it up. I asked myself, "How do I transfer this practice data into Hadoop using Jupyter?" 

That question was the beginning of the end of my simple crypto predictor. The moment I started looking at Big Data infrastructure, the scope of the project exploded. I realized that predicting a price based purely on historical numbers was flawed; markets move based on *news* and *sentiment*. 

I didn't just need a database. I needed a system that could read the news, store it, analyze it, and reason about it. I needed an AI.

Little did I know, this "simple" pivot would eventually lead to my own AI coding assistant sternly scolding me about Parquet partitioning, and my multi-agent pipeline confusing Tesla with interest rates in hilarious cross-talk hallucinations. But that's a story for later.

---
**Next:** [02 - First Prototype](02_First_Prototype.md) ➡️
