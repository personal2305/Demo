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

### Build the Knowledge Graph

1. Ensure Neo4j is running locally (default bolt URI `bolt://localhost:7687`).
2. Run the crawler and graph builder (replace `your_password`):

```bash
python crawl_and_build.py --neo4j-password your_password --max-pages 800
```

This will crawl the MOSDAC site, extract content, and populate Neo4j with `Page` and `Section` nodes.

After installing requirements, download the small English spaCy model (needed for entity extraction):

```bash
python -m spacy download en_core_web_sm
```

The entity extractor also leverages OpenStreetMap geocoding (via `geopy`). Ensure outbound Internet access is available or use `--no-entities` when running the CLI to skip geocoding.

### Build the Vector Search Index

After the Neo4j knowledge graph is populated, run:

```bash
export OPENAI_API_KEY="YOUR_OPENAI_KEY"
python build_vector_index.py --neo4j-password your_password --out vector_index
```

This will compute OpenAI embeddings for each `Section` node and store a FAISS index in `vector_index/`.

### Launch the Full Chatbot

Set environment variables (or edit `app.py` defaults):
```bash
export NEO4J_PASSWORD=your_password
export OPENAI_API_KEY=your_openai_key
streamlit run app.py
```