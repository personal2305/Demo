from __future__ import annotations

import logging
from typing import List

from neo4j import GraphDatabase

from .crawler import Page, Section
from .entities import EntityExtractor, Entity

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class KnowledgeGraphBuilder:
    """Utility class to push scraped MOSDAC content into Neo4j as a knowledge graph."""

    def __init__(self, uri: str, user: str, password: str, extractor: EntityExtractor | None = None):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
        self.extractor = extractor

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
                if self.extractor:
                    entities = self.extractor.extract(page.combined_text)
                    session.execute_write(self._attach_entities, page.url, entities)

    # ---------------------------------------------------------------------
    # Static transaction functions
    # ---------------------------------------------------------------------

    @staticmethod
    def _create_constraints(tx):
        tx.run("CREATE CONSTRAINT IF NOT EXISTS ON (p:Page) ASSERT p.url IS UNIQUE")
        tx.run("CREATE CONSTRAINT IF NOT EXISTS ON (s:Section) ASSERT (s.page_url, s.heading) IS UNIQUE")
        tx.run("CREATE CONSTRAINT IF NOT EXISTS ON (sat:Satellite) ASSERT sat.name IS UNIQUE")
        tx.run("CREATE CONSTRAINT IF NOT EXISTS ON (inst:Instrument) ASSERT inst.name IS UNIQUE")
        tx.run("CREATE CONSTRAINT IF NOT EXISTS ON (loc:Location) ASSERT loc.name IS UNIQUE")
        tx.run("CREATE POINT INDEX location_point_index IF NOT EXISTS FOR (l:Location) ON (l.location)")

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
    # Entity attachment transaction
    # ---------------------------------------------------------------------

    @staticmethod
    def _attach_entities(tx, page_url: str, entities: list[Entity]):
        for ent in entities:
            if ent.label == "SATELLITE":
                tx.run(
                    "MERGE (e:Satellite {name: $name}) "
                    "WITH e MATCH (p:Page {url: $page_url}) "
                    "MERGE (p)-[:MENTIONS]->(e)",
                    name=ent.text,
                    page_url=page_url,
                )
            elif ent.label == "INSTRUMENT":
                tx.run(
                    "MERGE (e:Instrument {name: $name}) "
                    "WITH e MATCH (p:Page {url: $page_url}) "
                    "MERGE (p)-[:MENTIONS]->(e)",
                    name=ent.text,
                    page_url=page_url,
                )
            elif ent.label == "LOCATION":
                params = {
                    "name": ent.text,
                    "page_url": page_url,
                    "latitude": ent.latitude,
                    "longitude": ent.longitude,
                }
                if ent.latitude is not None and ent.longitude is not None:
                    query = (
                        "MERGE (e:Location {name: $name}) "
                        "SET e.location = point({latitude: $latitude, longitude: $longitude}) "
                        "WITH e MATCH (p:Page {url: $page_url}) "
                        "MERGE (p)-[:MENTIONS]->(e)"
                    )
                else:
                    query = (
                        "MERGE (e:Location {name: $name}) "
                        "WITH e MATCH (p:Page {url: $page_url}) "
                        "MERGE (p)-[:MENTIONS]->(e)"
                    )
                tx.run(query, **params)

    # ---------------------------------------------------------------------
    # Convenience wrapper
    # ---------------------------------------------------------------------


def build_graph(pages: List[Page], uri: str, user: str, password: str, extractor: EntityExtractor | None = None):
    """High-level helper to build a knowledge graph and automatically close the driver."""
    builder = KnowledgeGraphBuilder(uri, user, password, extractor=extractor)
    try:
        builder.build_from_pages(pages)
    finally:
        builder.close()