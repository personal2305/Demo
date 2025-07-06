from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import List, Dict, Any

import openai
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS

from neo4j import GraphDatabase

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class QABot:
    """Retrieval-augmented Q&A engine over MOSDAC knowledge graph and FAISS index."""

    def __init__(
        self,
        neo4j_uri: str = "bolt://localhost:7687",
        neo4j_user: str = "neo4j",
        neo4j_password: str | None = None,
        vector_index_dir: str = "vector_index",
        openai_model: str = "gpt-3.5-turbo",
    ):
        self._driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_password))
        index_path = Path(vector_index_dir)
        if not index_path.exists():
            raise RuntimeError(
                f"Vector index directory '{vector_index_dir}' not found. Run build_vector_index.py first."
            )
        self._embedding = OpenAIEmbeddings()
        self._vector_store = FAISS.load_local(index_path.as_posix(), self._embedding, allow_dangerous_deserialization=True)
        self._openai_model = openai_model

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def answer(self, question: str, chat_history: List[Dict[str, str]] | None = None, top_k: int = 4) -> str:
        # 1. Retrieve relevant passages
        docs = self._vector_store.similarity_search(question, k=top_k)

        # 2. Gather structured facts from Neo4j for referenced pages
        page_urls = {doc.metadata.get("url") for doc in docs if doc.metadata.get("url")}
        facts = self._fetch_facts(page_urls)

        # 3. Compose prompt
        context_parts: List[str] = []
        for i, doc in enumerate(docs, 1):
            heading = doc.metadata.get("heading", "")
            context_parts.append(f"[Passage {i}] (Heading: {heading})\n{doc.page_content}")

        if facts:
            context_parts.append("\n[Structured Facts]\n" + "\n".join(facts))

        context = "\n\n".join(context_parts)[-4000:]

        system_prompt = (
            "You are an intelligent assistant for the MOSDAC satellite data portal. "
            "Use the provided context (web passages and structured facts) to answer the user question. "
            "If the answer is not contained in the context, say you do not know."
        )

        messages: List[Dict[str, str]] = [{"role": "system", "content": system_prompt}]
        if chat_history:
            for msg in chat_history[-6:]:  # include last few Q/A pairs for continuity
                messages.append(msg)
        messages.append({"role": "system", "content": f"Context:\n{context}"})
        messages.append({"role": "user", "content": question})

        logger.debug("Prompt tokens: %d", len(json.dumps(messages)))

        completion = openai.ChatCompletion.create(
            model=self._openai_model,
            messages=messages,
            temperature=0.2,
            max_tokens=512,
        )
        answer_text = completion.choices[0].message.content.strip()
        return answer_text

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _fetch_facts(self, page_urls: set[str]) -> List[str]:
        if not page_urls:
            return []
        query = (
            "MATCH (p:Page)-[:HAS_SECTION]->(s) WHERE p.url IN $urls "
            "OPTIONAL MATCH (p)-[:MENTIONS]->(e) "
            "RETURN DISTINCT p.url AS url, collect(distinct e.name) AS entities"
        )
        with self._driver.session() as session:
            res = session.run(query, urls=list(page_urls))
            facts: List[str] = []
            for record in res:
                url = record["url"]
                entities = [e for e in record["entities"] if e]
                if entities:
                    facts.append(f"Page {url} mentions: {', '.join(entities)}")
            return facts

    def close(self):
        self._driver.close()