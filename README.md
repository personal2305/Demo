# Demo

## MOSDAC AI Help Bot

This repository contains a prototype conversational assistant for the MOSDAC portal.

### Quickstart

1. Create and activate a Python 3.10+ virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. (Optional) Export your LLM API key if you intend to wire in a real backend:

```bash
export OPENAI_API_KEY="YOUR_KEY_HERE"
```

4. Launch the Streamlit application:

```bash
streamlit run app.py
```

5. A browser window will open where you can chat with the bot.

### Next Steps

* Integrate web scraping and knowledge-graph construction from the MOSDAC portal.
* Replace the placeholder `get_answer` function with retrieval-augmented generation (RAG) powered by an LLM.
* Add geospatial reasoning modules for spatially-aware Q&A.
* Package the solution for deployment across other web portals.