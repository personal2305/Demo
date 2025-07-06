import spacy
import re
import logging
from transformers import AutoTokenizer, AutoModel
from sentence_transformers import SentenceTransformer
import torch
import numpy as np
from typing import Dict, List, Tuple, Any

logger = logging.getLogger(__name__)

class NLPProcessor:
    """Natural Language Processing component for query understanding and entity extraction"""
    
    def __init__(self):
        self.setup_models()
        self.intent_patterns = self._load_intent_patterns()
        self.geospatial_keywords = [
            'location', 'coordinates', 'latitude', 'longitude', 'region', 'area',
            'boundary', 'map', 'satellite', 'imagery', 'coverage', 'extent',
            'polygon', 'point', 'geometry', 'spatial', 'geographic'
        ]
        
    def setup_models(self):
        """Initialize NLP models and components"""
        try:
            # Load spaCy model for NER and dependency parsing
            try:
                self.nlp = spacy.load("en_core_web_sm")
            except OSError:
                logger.warning("en_core_web_sm not found, using blank model")
                self.nlp = spacy.blank("en")
                
            # Load sentence transformer for semantic similarity
            self.sentence_model = SentenceTransformer('all-MiniLM-L6-v2')
            
            logger.info("NLP models loaded successfully")
            
        except Exception as e:
            logger.error(f"Error loading NLP models: {str(e)}")
            raise
    
    def _load_intent_patterns(self) -> Dict[str, List[str]]:
        """Load intent classification patterns"""
        return {
            'data_request': [
                r'download.*data', r'get.*dataset', r'access.*data', r'retrieve.*data',
                r'where.*can.*find', r'how.*to.*download', r'data.*available'
            ],
            'information_query': [
                r'what.*is', r'explain', r'describe', r'tell.*me.*about',
                r'information.*about', r'details.*about', r'how.*does.*work'
            ],
            'geospatial_query': [
                r'location.*of', r'coordinates.*of', r'map.*of', r'coverage.*area',
                r'satellite.*image', r'boundary.*of', r'region.*of'
            ],
            'technical_support': [
                r'error.*occurred', r'problem.*with', r'not.*working', r'help.*with',
                r'troubleshoot', r'fix.*issue', r'support'
            ],
            'navigation_help': [
                r'how.*to.*navigate', r'find.*page', r'where.*is.*menu',
                r'go.*to', r'access.*section', r'locate.*feature'
            ]
        }
    
    def process_query(self, query: str) -> Dict[str, Any]:
        """Process user query and extract relevant information"""
        try:
            # Clean and normalize query
            cleaned_query = self._clean_query(query)
            
            # Extract entities
            entities = self._extract_entities(cleaned_query)
            
            # Classify intent
            intent = self._classify_intent(cleaned_query)
            
            # Extract keywords
            keywords = self._extract_keywords(cleaned_query)
            
            # Check for geospatial elements
            is_geospatial = self._is_geospatial_query(cleaned_query)
            
            # Generate query embedding
            embedding = self._get_query_embedding(cleaned_query)
            
            return {
                'original_query': query,
                'cleaned_query': cleaned_query,
                'entities': entities,
                'intent': intent,
                'keywords': keywords,
                'is_geospatial': is_geospatial,
                'embedding': embedding,
                'confidence': self._calculate_confidence(entities, intent, keywords)
            }
            
        except Exception as e:
            logger.error(f"Error processing query: {str(e)}")
            return self._get_default_query_result(query)
    
    def _clean_query(self, query: str) -> str:
        """Clean and normalize the input query"""
        # Remove extra whitespace
        query = re.sub(r'\s+', ' ', query.strip())
        
        # Convert to lowercase for processing
        query = query.lower()
        
        # Remove special characters except essential ones
        query = re.sub(r'[^\w\s\-\.\?\!\,]', ' ', query)
        
        return query
    
    def _extract_entities(self, query: str) -> List[Dict[str, Any]]:
        """Extract named entities from the query"""
        doc = self.nlp(query)
        entities = []
        
        for ent in doc.ents:
            entities.append({
                'text': ent.text,
                'label': ent.label_,
                'start': ent.start_char,
                'end': ent.end_char,
                'confidence': 1.0  # spaCy doesn't provide confidence scores by default
            })
        
        # Add custom entity extraction for domain-specific terms
        domain_entities = self._extract_domain_entities(query)
        entities.extend(domain_entities)
        
        return entities
    
    def _extract_domain_entities(self, query: str) -> List[Dict[str, Any]]:
        """Extract domain-specific entities relevant to MOSDAC"""
        entities = []
        
        # Satellite/sensor patterns
        satellite_patterns = [
            r'(landsat|sentinel|modis|aster|cartosat|resourcesat|oceansat)',
            r'(l1|l2|l3|l4)\s*(data|product)',
            r'(visible|infrared|thermal|microwave)\s*(band|channel)'
        ]
        
        # Data product patterns
        product_patterns = [
            r'(ndvi|ndwi|lst|sst|chlorophyll|aerosol)',
            r'(dem|dtm|dsm)',
            r'(precipitation|temperature|humidity)\s*(data|product)'
        ]
        
        # Geographic patterns
        geo_patterns = [
            r'(india|indian\s*ocean|arabian\s*sea|bay\s*of\s*bengal)',
            r'(state|district|city|region)\s*of\s*\w+',
            r'\d+\.?\d*\s*(north|south|east|west|n|s|e|w|lat|lon|latitude|longitude)'
        ]
        
        all_patterns = satellite_patterns + product_patterns + geo_patterns
        pattern_types = ['SATELLITE'] * len(satellite_patterns) + \
                       ['PRODUCT'] * len(product_patterns) + \
                       ['GEO'] * len(geo_patterns)
        
        for pattern, entity_type in zip(all_patterns, pattern_types):
            matches = re.finditer(pattern, query, re.IGNORECASE)
            for match in matches:
                entities.append({
                    'text': match.group(),
                    'label': entity_type,
                    'start': match.start(),
                    'end': match.end(),
                    'confidence': 0.8
                })
        
        return entities
    
    def _classify_intent(self, query: str) -> Dict[str, float]:
        """Classify the intent of the user query"""
        intent_scores = {}
        
        for intent, patterns in self.intent_patterns.items():
            score = 0.0
            for pattern in patterns:
                if re.search(pattern, query, re.IGNORECASE):
                    score += 1.0
            
            # Normalize score
            intent_scores[intent] = score / len(patterns) if patterns else 0.0
        
        # If no clear intent, classify as information_query
        if not any(score > 0.3 for score in intent_scores.values()):
            intent_scores['information_query'] = 0.5
        
        return intent_scores
    
    def _extract_keywords(self, query: str) -> List[str]:
        """Extract important keywords from the query"""
        doc = self.nlp(query)
        keywords = []
        
        # Extract meaningful tokens (nouns, verbs, adjectives)
        for token in doc:
            if (token.pos_ in ['NOUN', 'VERB', 'ADJ'] and 
                not token.is_stop and 
                not token.is_punct and 
                len(token.text) > 2):
                keywords.append(token.lemma_)
        
        # Remove duplicates while preserving order
        keywords = list(dict.fromkeys(keywords))
        
        return keywords
    
    def _is_geospatial_query(self, query: str) -> bool:
        """Check if the query has geospatial intent"""
        return any(keyword in query for keyword in self.geospatial_keywords)
    
    def _get_query_embedding(self, query: str) -> np.ndarray:
        """Generate semantic embedding for the query"""
        try:
            embedding = self.sentence_model.encode(query)
            return embedding
        except Exception as e:
            logger.warning(f"Error generating embedding: {str(e)}")
            return np.zeros(384)  # Default dimension for all-MiniLM-L6-v2
    
    def _calculate_confidence(self, entities: List[Dict], intent: Dict[str, float], 
                            keywords: List[str]) -> float:
        """Calculate overall confidence score for query processing"""
        entity_confidence = np.mean([e['confidence'] for e in entities]) if entities else 0.3
        intent_confidence = max(intent.values()) if intent else 0.3
        keyword_confidence = min(len(keywords) / 5, 1.0)  # Normalize to max 1.0
        
        # Weighted average
        overall_confidence = (entity_confidence * 0.4 + 
                            intent_confidence * 0.4 + 
                            keyword_confidence * 0.2)
        
        return min(overall_confidence, 1.0)
    
    def _get_default_query_result(self, query: str) -> Dict[str, Any]:
        """Return default result for failed query processing"""
        return {
            'original_query': query,
            'cleaned_query': query.lower().strip(),
            'entities': [],
            'intent': {'information_query': 0.5},
            'keywords': query.lower().split(),
            'is_geospatial': False,
            'embedding': np.zeros(384),
            'confidence': 0.3
        }
    
    def get_semantic_similarity(self, query1: str, query2: str) -> float:
        """Calculate semantic similarity between two queries"""
        try:
            embeddings = self.sentence_model.encode([query1, query2])
            similarity = np.dot(embeddings[0], embeddings[1]) / (
                np.linalg.norm(embeddings[0]) * np.linalg.norm(embeddings[1])
            )
            return float(similarity)
        except Exception as e:
            logger.error(f"Error calculating similarity: {str(e)}")
            return 0.0