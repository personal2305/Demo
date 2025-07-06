from __future__ import annotations

import functools
import logging
from dataclasses import dataclass
from typing import List, Set

import spacy
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderServiceError
from spacy.matcher import PhraseMatcher

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


@dataclass
class Entity:
    text: str
    label: str  # SATELLITE, INSTRUMENT, LOCATION
    latitude: float | None = None
    longitude: float | None = None


class EntityExtractor:
    """Extract satellites, instruments, and locations from free text."""

    # Example wordlists. Extend/replace with authoritative data sets.
    SATELLITE_TERMS = [
        "INSAT-3D",
        "INSAT-3DR",
        "SCATSAT-1",
        "Cartosat-3",
        "Oceansat-2",
        "RISAT-1",
        "Chandrayaan-2",
        "Megha-Tropiques",
        "SARAL",
    ]

    INSTRUMENT_TERMS = [
        "CCD camera",
        "Ocean Colour Monitor",
        "Scatterometer",
        "Sounder",
        "Imager",
        "AWiFS",
        "LISS-III",
        "LISS-IV",
    ]

    def __init__(self, enable_geocoding: bool = True):
        self.enable_geocoding = enable_geocoding
        logger.info("Loading spaCy model 'en_core_web_sm'…")
        try:
            self.nlp = spacy.load("en_core_web_sm")
        except OSError:
            logger.error(
                "spaCy model 'en_core_web_sm' not found. Please run: python -m spacy download en_core_web_sm"
            )
            raise

        # Build custom phrase matcher for satellites and instruments
        self.matcher = PhraseMatcher(self.nlp.vocab, attr="LOWER")
        self.matcher.add("SATELLITE", [self.nlp.make_doc(term) for term in self.SATELLITE_TERMS])
        self.matcher.add("INSTRUMENT", [self.nlp.make_doc(term) for term in self.INSTRUMENT_TERMS])

        # Setup geocoder
        self._geocode = self._make_geocoder() if enable_geocoding else lambda name: (None, None)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def extract(self, text: str) -> List[Entity]:
        doc = self.nlp(text)
        entities: List[Entity] = []

        # Custom phrase matcher
        matches = self.matcher(doc)
        for match_id, start, end in matches:
            label = self.nlp.vocab.strings[match_id]
            span = doc[start:end]
            entities.append(Entity(text=span.text, label=label))

        # Built-in NER for locations
        for ent in doc.ents:
            if ent.label_ in {"GPE", "LOC", "FAC"}:
                lat, lon = self._geocode(ent.text) if self.enable_geocoding else (None, None)
                entities.append(Entity(text=ent.text, label="LOCATION", latitude=lat, longitude=lon))

        # Deduplicate by (text, label)
        seen: Set[tuple[str, str]] = set()
        deduped: List[Entity] = []
        for ent in entities:
            key = (ent.text.lower(), ent.label)
            if key not in seen:
                seen.add(key)
                deduped.append(ent)
        return deduped

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _make_geocoder():
        geolocator = Nominatim(user_agent="mosdac_bot_geocoder", timeout=10)

        @functools.lru_cache(maxsize=512)
        def _geocode(name: str):
            try:
                loc = geolocator.geocode(name)
                if loc:
                    return loc.latitude, loc.longitude
            except GeocoderServiceError as e:
                logger.warning("Geocoding error for '%s': %s", name, e)
            return None, None

        return _geocode