import logging
import re
import time
from collections import deque
from dataclasses import dataclass, field
from typing import List, Optional, Set
from urllib.parse import urljoin, urldefrag, urlparse

import requests
from bs4 import BeautifulSoup, NavigableString

# Configure root logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

DEFAULT_HEADERS = {
    "User-Agent": "MOSDAC-Bot/0.1 (+https://github.com/your-org/mosdac-bot)"
}

# Regex patterns to identify media/content we want to ignore
FILE_EXT_BLACKLIST = re.compile(
    r"\.(jpg|jpeg|png|gif|tif|tiff|bmp|svg|ico|css|js|json|xml|zip|gz|tgz|rar|tar|7z)$",
    re.IGNORECASE,
)


@dataclass
class Section:
    """Represents an HTML heading and its textual paragraph content."""

    heading: str
    text: str


@dataclass
class Page:
    """Represents a crawled page with its extracted content."""

    url: str
    title: Optional[str] = None
    sections: List[Section] = field(default_factory=list)
    raw_html: Optional[str] = None

    @property
    def combined_text(self) -> str:
        texts = [self.title or ""] + [s.heading + "\n" + s.text for s in self.sections]
        return "\n\n".join(texts).strip()


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------


def is_same_domain(start_netloc: str, candidate_url: str) -> bool:
    try:
        return urlparse(candidate_url).netloc == start_netloc
    except Exception:
        return False


def normalize_url(base_url: str, link: str) -> Optional[str]:
    if not link:
        return None
    link = urljoin(base_url, link)
    link, _ = urldefrag(link)  # strip out URL fragments
    if FILE_EXT_BLACKLIST.search(link):
        return None
    return link


# ---------------------------------------------------------------------------
# Core crawling routine
# ---------------------------------------------------------------------------


def crawl_site(base_url: str, max_pages: int = 500, delay: float = 0.5) -> List[Page]:
    """Breadth-first crawl of the MOSDAC website.

    Parameters
    ----------
    base_url : str
        Root URL to start crawling (e.g., "https://www.mosdac.gov.in/")
    max_pages : int, optional
        Maximum number of pages to crawl. Defaults to 500.
    delay : float, optional
        Delay between requests in seconds, to be polite. Defaults to 0.5.

    Returns
    -------
    List[Page]
        Pages with extracted content (title, headings, body text).
    """
    visited: Set[str] = set()
    queue: deque[str] = deque([base_url])
    pages: List[Page] = []
    netloc = urlparse(base_url).netloc

    session = requests.Session()
    session.headers.update(DEFAULT_HEADERS)

    while queue and len(pages) < max_pages:
        url = queue.popleft()
        if url in visited:
            continue
        visited.add(url)
        logger.info("Fetching %s", url)
        try:
            resp = session.get(url, timeout=15)
            resp.raise_for_status()
        except Exception as exc:
            logger.warning("Failed to fetch %s: %s", url, exc)
            continue

        soup = BeautifulSoup(resp.text, "lxml")
        title = soup.title.string.strip() if soup.title and soup.title.string else None

        # Extract headings (h1-h3) and associated paragraphs
        sections: List[Section] = []
        for heading_tag in soup.find_all(["h1", "h2", "h3"]):
            heading_text = heading_tag.get_text(strip=True)
            section_parts: List[str] = []
            for sibling in heading_tag.next_siblings:
                if sibling.name and sibling.name.startswith("h"):
                    break  # next section
                if isinstance(sibling, NavigableString):
                    section_parts.append(sibling.strip())
                elif sibling.name in ["p", "li", "span", "div"]:
                    section_parts.append(sibling.get_text(" ", strip=True))
            paragraph_text = " ".join(part for part in section_parts if part)
            if paragraph_text:
                sections.append(Section(heading=heading_text, text=paragraph_text))

        page = Page(url=url, title=title, sections=sections, raw_html=resp.text)
        pages.append(page)

        # Find new links to follow
        for link_tag in soup.find_all("a", href=True):
            link_url = normalize_url(url, link_tag["href"])
            if not link_url:
                continue
            if is_same_domain(netloc, link_url) and link_url not in visited:
                queue.append(link_url)

        time.sleep(delay)

    return pages