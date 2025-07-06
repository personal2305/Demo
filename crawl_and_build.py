import argparse
import logging

from mosdac_bot import crawl_site, build_graph

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")


def main():
    parser = argparse.ArgumentParser(description="Crawl MOSDAC and build a Neo4j knowledge graph.")
    parser.add_argument("--neo4j-password", required=True, help="Password for the Neo4j user")
    parser.add_argument("--neo4j-uri", default="bolt://localhost:7687", help="Neo4j bolt URI")
    parser.add_argument("--neo4j-user", default="neo4j", help="Neo4j username")
    parser.add_argument("--base-url", default="https://www.mosdac.gov.in/", help="Start URL to crawl")
    parser.add_argument("--max-pages", type=int, default=500, help="Maximum number of pages to crawl")
    parser.add_argument("--delay", type=float, default=0.5, help="Delay between requests (seconds)")
    args = parser.parse_args()

    pages = crawl_site(args.base_url, max_pages=args.max_pages, delay=args.delay)
    logging.info("Crawled %d pages. Building knowledge graph…", len(pages))
    build_graph(pages, args.neo4j_uri, args.neo4j_user, args.neo4j_password)
    logging.info("Knowledge graph construction completed.")


if __name__ == "__main__":
    main()