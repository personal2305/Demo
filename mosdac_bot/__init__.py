from importlib.metadata import version, PackageNotFoundError

try:
    __version__ = version("mosdac_bot")
except PackageNotFoundError:
    __version__ = "0.0.0"

# Re-export core APIs
from .crawler import crawl_site, Page
from .graph_builder import build_graph

__all__ = [
    "crawl_site",
    "Page",
    "build_graph",
]