import logging
import re
from typing import Dict, List, Any
import spacy
from datetime import datetime

logger = logging.getLogger(__name__)

class ContentProcessor:
    """Process and structure scraped web content for knowledge graph integration"""
    
    def __init__(self):
        self.setup_nlp()
        
    def setup_nlp(self):
        """Initialize NLP components"""
        try:
            self.nlp = spacy.load("en_core_web_sm")
        except OSError:
            logger.warning("spaCy model not found, using basic processing")
            self.nlp = None
    
    def process_content(self, scraped_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Process scraped content and extract structured information"""
        processed_content = []
        
        for item in scraped_data:
            try:
                processed_item = self._process_single_item(item)
                if processed_item:
                    processed_content.append(processed_item)
            except Exception as e:
                logger.error(f"Error processing item {item.get('url', 'unknown')}: {str(e)}")
                continue
        
        return processed_content
    
    def _process_single_item(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """Process a single scraped item"""
        # Extract entities and relationships
        entities = self._extract_entities(item)
        relationships = self._extract_relationships(item)
        
        # Clean and enhance content
        cleaned_content = self._clean_content(item.get('content', ''))
        enhanced_keywords = self._enhance_keywords(item.get('keywords', []), cleaned_content)
        
        return {
            'url': item.get('url'),
            'title': item.get('title'),
            'description': item.get('description'),
            'content': cleaned_content,
            'keywords': enhanced_keywords,
            'entities': entities,
            'relationships': relationships,
            'page_type': item.get('page_type'),
            'processed_at': datetime.now().isoformat()
        }
    
    def _extract_entities(self, item: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract named entities from content"""
        entities = []
        content = f"{item.get('title', '')} {item.get('content', '')}"
        
        if self.nlp:
            doc = self.nlp(content[:1000000])  # Limit text length
            for ent in doc.ents:
                entities.append({
                    'text': ent.text,
                    'label': ent.label_,
                    'start': ent.start_char,
                    'end': ent.end_char
                })
        
        # Add domain-specific entities
        domain_entities = self._extract_domain_entities(content)
        entities.extend(domain_entities)
        
        return entities
    
    def _extract_domain_entities(self, content: str) -> List[Dict[str, Any]]:
        """Extract domain-specific entities for MOSDAC"""
        entities = []
        content_lower = content.lower()
        
        # Satellite patterns
        satellite_patterns = [
            (r'\b(oceansat[-\s]?[12]?)\b', 'SATELLITE'),
            (r'\b(resourcesat[-\s]?[12]?)\b', 'SATELLITE'),
            (r'\b(insat[-\s]?3[a-z]?)\b', 'SATELLITE'),
            (r'\b(cartosat[-\s]?[12]?)\b', 'SATELLITE'),
            (r'\b(landsat[-\s]?[4-8]?)\b', 'SATELLITE'),
            (r'\b(sentinel[-\s]?[12]?)\b', 'SATELLITE'),
            (r'\b(modis)\b', 'SATELLITE')
        ]
        
        # Data product patterns
        product_patterns = [
            (r'\b(ocean\s+color)\b', 'PRODUCT'),
            (r'\b(sea\s+surface\s+temperature|sst)\b', 'PRODUCT'),
            (r'\b(land\s+surface\s+temperature|lst)\b', 'PRODUCT'),
            (r'\b(ndvi)\b', 'PRODUCT'),
            (r'\b(chlorophyll)\b', 'PRODUCT'),
            (r'\b(precipitation)\b', 'PRODUCT'),
            (r'\b(wind\s+speed)\b', 'PRODUCT')
        ]
        
        all_patterns = satellite_patterns + product_patterns
        
        for pattern, entity_type in all_patterns:
            matches = re.finditer(pattern, content_lower)
            for match in matches:
                entities.append({
                    'text': match.group(),
                    'label': entity_type,
                    'start': match.start(),
                    'end': match.end()
                })
        
        return entities
    
    def _extract_relationships(self, item: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract relationships between entities"""
        relationships = []
        # This is a simplified version - would need more sophisticated NLP
        return relationships
    
    def _clean_content(self, content: str) -> str:
        """Clean and normalize content text"""
        if not content:
            return ""
        
        # Remove extra whitespace
        content = re.sub(r'\s+', ' ', content)
        
        # Remove special characters but keep basic punctuation
        content = re.sub(r'[^\w\s\.\,\!\?\-\(\)]', ' ', content)
        
        # Remove very short or very long words
        words = content.split()
        cleaned_words = [word for word in words if 2 <= len(word) <= 50]
        
        return ' '.join(cleaned_words).strip()
    
    def _enhance_keywords(self, existing_keywords: List[str], content: str) -> List[str]:
        """Enhance keywords with content analysis"""
        enhanced = existing_keywords.copy()
        
        # Add important terms from content
        if self.nlp:
            doc = self.nlp(content[:100000])  # Limit for performance
            for token in doc:
                if (token.pos_ in ['NOUN', 'PROPN'] and 
                    not token.is_stop and 
                    len(token.text) > 3 and
                    token.text.lower() not in enhanced):
                    enhanced.append(token.text.lower())
        
        return enhanced[:30]  # Limit keywords