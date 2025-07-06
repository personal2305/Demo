from __future__ import annotations

import logging
from typing import List

from neo4j import GraphDatabase

from .crawler import Page, Section

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class KnowledgeGraphBuilder:
    """Utility class to push scraped MOSDAC content into Neo4j as a knowledge graph."""

    def __init__(self, uri: str, user: str, password: str):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        self.driver.close()

    # ---------------------------------------------------------------------
    # Public API
    # ---------------------------------------------------------------------

    def build_from_pages(self, pages: List[Page]):
        """Ingest a list of `Page` objects into the graph."""
        with self.driver.session() as session:
            session.execute_write(self._create_constraints)
            for page in pages:
                session.execute_write(self._create_page_node, page)

    # ---------------------------------------------------------------------
    # Static transaction functions
    # ---------------------------------------------------------------------

    @staticmethod
    def _create_constraints(tx):
        tx.run("CREATE CONSTRAINT IF NOT EXISTS ON (p:Page) ASSERT p.url IS UNIQUE")
        tx.run("CREATE CONSTRAINT IF NOT EXISTS ON (s:Section) ASSERT (s.page_url, s.heading) IS UNIQUE")

    @staticmethod
    def _create_page_node(tx, page: Page):
        logger.debug("Creating Page node for %s", page.url)
        # Create the page node
        tx.run(
            "MERGE (p:Page {url: $url}) "
            "SET p.title = $title",
            url=page.url,
            title=page.title or "",
        )

        # Create Section nodes and relationships
        for idx, section in enumerate(page.sections):
            tx.run(
                "MERGE (s:Section {page_url: $page_url, heading: $heading}) "
                "SET s.text = $text, s.idx = $idx "
                "WITH s "
                "MATCH (p:Page {url: $page_url}) "
                "MERGE (p)-[:HAS_SECTION]->(s)",
                page_url=page.url,
                heading=section.heading,
                text=section.text,
                idx=idx,
            )

    # ---------------------------------------------------------------------
    # Convenience wrapper
    # ---------------------------------------------------------------------


def build_graph(pages: List[Page], uri: str, user: str, password: str):
    """High-level helper to build a knowledge graph and automatically close the driver."""
    builder = KnowledgeGraphBuilder(uri, user, password)
    try:
        builder.build_from_pages(pages)
    finally:
        builder.close()