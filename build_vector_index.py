import argparse
import logging
import os
from typing import List

import openai
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.docstore.document import Document
from neo4j import GraphDatabase
from tqdm import tqdm

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("vector_index_builder")


def fetch_sections(uri: str, user: str, password: str, limit: int | None = None) -> List[Document]:
    """Fetch Section nodes from Neo4j and map them to LangChain Documents."""
    driver = GraphDatabase.driver(uri, auth=(user, password))
    docs: List[Document] = []
    query = (
        "MATCH (s:Section)<-[:HAS_SECTION]-(p:Page) "
        "RETURN s.text AS text, p.url AS url, s.heading AS heading, s.idx AS idx "
        + ("LIMIT $limit" if limit else "")
    )
    with driver.session() as session:
        res = session.run(query, limit=limit)
        for record in res:
            metadata = {
                "url": record["url"],
                "heading": record["heading"],
                "idx": record["idx"],
            }
            docs.append(Document(page_content=record["text"], metadata=metadata))
    driver.close()
    return docs


def build_faiss_index(docs: List[Document], output_dir: str):
    os.makedirs(output_dir, exist_ok=True)
    embeddings = OpenAIEmbeddings()
    logger.info("Generating embeddings (%d documents)…", len(docs))
    # progress
    texts = [d.page_content for d in docs]
    metadatas = [d.metadata for d in docs]
    index = FAISS.from_texts(texts=texts, embedding=embeddings, metadatas=metadatas)
    index.save_local(output_dir)
    logger.info("Vector index saved to %s", output_dir)


def main():
    parser = argparse.ArgumentParser(description="Build FAISS vector index from Neo4j content")
    parser.add_argument("--neo4j-uri", default="bolt://localhost:7687")
    parser.add_argument("--neo4j-user", default="neo4j")
    parser.add_argument("--neo4j-password", required=True)
    parser.add_argument("--limit", type=int, default=None, help="Limit number of sections for indexing")
    parser.add_argument("--out", default="vector_index", help="Output directory for FAISS index")
    args = parser.parse_args()

    # Ensure API key
    if not os.getenv("OPENAI_API_KEY"):
        logger.error("OPENAI_API_KEY environment variable not set.")
        return

    docs = fetch_sections(args.neo4j_uri, args.neo4j_user, args.neo4j_password, limit=args.limit)
    if not docs:
        logger.error("No documents fetched from Neo4j. Has the graph been built?")
        return

    build_faiss_index(docs, args.out)


if __name__ == "__main__":
    main()