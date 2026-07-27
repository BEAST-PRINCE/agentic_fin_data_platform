# 15 - Developer Journey

Code tells you *how* a system works. Documentation tells you *what* a system does. But neither of them tells you *what it felt like* to build it.

When you look at a polished architecture diagram like the one in `03_System_Architecture.md`, it looks like everything was perfectly planned from day one. It wasn't. This project evolved through a series of late nights, broken pipelines, PyTorch memory leaks, and LLM hallucinations. I wanted to capture that reality.

## 📖 The Engineering Journal

I maintain a chronological engineering journal of this project. Instead of hiding the mistakes, I documented them. The full, raw logs are stored in the **`docs/developer_journey/`** directory.

To give you an idea of what it took to build this, here are the major "eras" of the project's evolution, drawn directly from my chat logs and Git history.

### Era 1: The Messy Beginnings (Scripts and Syntax Errors)
This project didn't start as a multi-agent lakehouse. It started as a messy Jupyter Notebook (`data_creation.ipynb`) where I was just trying to generate practice data and build a simple cryptocurrency price predictor. The early days were spent modularizing basic scripts (`data_utils.py`, `model_utils.py`), fighting with Docker Compose YAML indentation errors (Line 27 will haunt me forever), and trying to figure out how to push data into a local Hadoop cluster before eventually discovering MinIO.

### Era 2: The Great Lakehouse Refactor (and Stalling Pipelines)
Once I had data flowing, I realized simple Pandas dataframes couldn't handle the scale. I transitioned to the Medallion Architecture using PySpark. 
This was a painful transition. I spent days debugging a "silent exception" in my PySpark job that was causing the Gold layer pipeline to completely stall. The job was silently failing and falling back to a massively slow "full-load" process instead of an incremental update because of corrupted S3 data in the Bronze bucket. Fixing that incremental logic was the turning point for the pipeline's stability.

### Era 3: The AI Integration (Deadlocks and Hallucinations)
Integrating Qdrant and the Sentence Transformers was the next hurdle. I decided to run the embeddings locally to save money. This immediately introduced catastrophic PyTorch/OpenMP threading deadlocks when FastAPI async workers collided with the C++ backend of the embedding models. I had to completely restructure the API to load the models strictly on the main thread during the startup event.
At the same time, I was fighting with the agents. Early versions of the Planner agent would hallucinate tools that didn't exist or pass strings into integer fields. Enforcing strict JSON schemas via MCP was born out of pure frustration.

### Era 4: The Dashboard & Observability Polish
The final era was about making it usable. Staring at terminal logs wasn't cutting it. I built the React/Vite dashboard. The biggest breakthrough here was the "Agent Workflow" accordion. Originally, the dashboard just hung for 30 seconds while the agents thought, leaving the user wondering if it crashed. By streaming the intermediate, non-human-readable JSON steps into a beautiful UI, the latency suddenly felt like a feature, not a bug. 
I also spent significant time fixing session isolation issues—if you asked two questions quickly, the agents would corrupt each other's context. Implementing proper conversational boundaries and Prometheus timing metrics finally made the system feel like a mature product.

### Why read the full logs?
* **For Data Engineers:** You'll see the exact moment I realized my Parquet files were too small and crashing DuckDB, and how I fixed the Spark partitioning.
* **For AI Engineers:** You'll see the prompt engineering struggles in real-time.
* **For Builders:** It's proof that complex systems are just simple systems that evolved through trial, error, and relentless refactoring.

Go to the `docs/developer_journey/` folder to start from Day 1.

---
⬅️ **Previous:** [14 - Project Decisions](14_Project_Decisions.md) | **Next:** [16 - Performance and Scaling](16_Performance_and_Scaling.md) ➡️
