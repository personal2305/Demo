import networkx as nx
import json
import pickle
import logging
from typing import Dict, List, Any, Tuple, Optional
import numpy as np
from datetime import datetime
import os
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

logger = logging.getLogger(__name__)

class KnowledgeGraph:
    """Knowledge Graph for storing and retrieving structured information"""
    
    def __init__(self, graph_path: str = "data/knowledge_graph.pkl"):
        self.graph_path = graph_path
        self.graph = nx.MultiDiGraph()
        self.embeddings = {}
        self.entity_types = set()
        self.relationship_types = set()
        self.sentence_model = SentenceTransformer('all-MiniLM-L6-v2')
        
        # Load existing graph if available
        self.load_graph()
        
    def load_graph(self):
        """Load existing knowledge graph from disk"""
        try:
            if os.path.exists(self.graph_path):
                with open(self.graph_path, 'rb') as f:
                    data = pickle.load(f)
                    self.graph = data.get('graph', nx.MultiDiGraph())
                    self.embeddings = data.get('embeddings', {})
                    self.entity_types = data.get('entity_types', set())
                    self.relationship_types = data.get('relationship_types', set())
                logger.info(f"Loaded knowledge graph with {self.graph.number_of_nodes()} nodes")
            else:
                logger.info("No existing knowledge graph found, starting fresh")
                self._initialize_base_knowledge()
                
        except Exception as e:
            logger.error(f"Error loading knowledge graph: {str(e)}")
            self._initialize_base_knowledge()
    
    def save_graph(self):
        """Save knowledge graph to disk"""
        try:
            os.makedirs(os.path.dirname(self.graph_path), exist_ok=True)
            data = {
                'graph': self.graph,
                'embeddings': self.embeddings,
                'entity_types': self.entity_types,
                'relationship_types': self.relationship_types,
                'last_updated': datetime.now().isoformat()
            }
            with open(self.graph_path, 'wb') as f:
                pickle.dump(data, f)
            logger.info("Knowledge graph saved successfully")
        except Exception as e:
            logger.error(f"Error saving knowledge graph: {str(e)}")
    
    def _initialize_base_knowledge(self):
        """Initialize base knowledge about MOSDAC and satellite data"""
        base_entities = [
            {
                'id': 'mosdac',
                'type': 'ORGANIZATION',
                'name': 'MOSDAC',
                'description': 'Meteorological and Oceanographic Satellite Data Archival Centre',
                'attributes': {
                    'url': 'https://www.mosdac.gov.in',
                    'parent_org': 'ISRO',
                    'established': '2008'
                }
            },
            {
                'id': 'satellite_data',
                'type': 'DATA_CATEGORY',
                'name': 'Satellite Data',
                'description': 'Earth observation data from various satellites',
                'attributes': {}
            },
            {
                'id': 'oceansat',
                'type': 'SATELLITE',
                'name': 'Oceansat',
                'description': 'Indian satellite for ocean and atmospheric studies',
                'attributes': {
                    'launch_year': '2009',
                    'sensors': ['OCM', 'SCAT', 'ROSA']
                }
            },
            {
                'id': 'resourcesat',
                'type': 'SATELLITE',
                'name': 'ResourceSat',
                'description': 'Indian Earth observation satellite',
                'attributes': {
                    'sensors': ['LISS-III', 'LISS-IV', 'AWiFS']
                }
            }
        ]
        
        # Add base entities
        for entity in base_entities:
            self.add_entity(entity)
        
        # Add base relationships
        self.add_relationship('mosdac', 'provides', 'satellite_data')
        self.add_relationship('oceansat', 'generates', 'satellite_data')
        self.add_relationship('resourcesat', 'generates', 'satellite_data')
        self.add_relationship('satellite_data', 'stored_in', 'mosdac')
        
        logger.info("Initialized base knowledge graph")
    
    def add_entity(self, entity: Dict[str, Any]) -> str:
        """Add an entity to the knowledge graph"""
        try:
            entity_id = entity['id']
            entity_type = entity['type']
            
            # Add node to graph
            self.graph.add_node(
                entity_id,
                type=entity_type,
                name=entity.get('name', entity_id),
                description=entity.get('description', ''),
                attributes=entity.get('attributes', {}),
                created_at=datetime.now().isoformat()
            )
            
            # Generate and store embedding
            text_for_embedding = f"{entity.get('name', '')} {entity.get('description', '')}"
            if text_for_embedding.strip():
                embedding = self.sentence_model.encode(text_for_embedding)
                self.embeddings[entity_id] = embedding
            
            # Track entity type
            self.entity_types.add(entity_type)
            
            logger.debug(f"Added entity: {entity_id}")
            return entity_id
            
        except Exception as e:
            logger.error(f"Error adding entity: {str(e)}")
            return None
    
    def add_relationship(self, source_id: str, relationship: str, target_id: str, 
                        attributes: Dict = None) -> bool:
        """Add a relationship between two entities"""
        try:
            if source_id not in self.graph or target_id not in self.graph:
                logger.warning(f"Cannot add relationship: missing entities {source_id} or {target_id}")
                return False
            
            self.graph.add_edge(
                source_id,
                target_id,
                relationship=relationship,
                attributes=attributes or {},
                created_at=datetime.now().isoformat()
            )
            
            self.relationship_types.add(relationship)
            logger.debug(f"Added relationship: {source_id} -> {relationship} -> {target_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error adding relationship: {str(e)}")
            return False
    
    def search(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search the knowledge graph using semantic similarity"""
        try:
            if not query.strip():
                return []
            
            # Generate query embedding
            query_embedding = self.sentence_model.encode(query)
            
            # Calculate similarities with all entities
            similarities = []
            for entity_id, embedding in self.embeddings.items():
                if entity_id in self.graph:
                    similarity = cosine_similarity(
                        query_embedding.reshape(1, -1),
                        embedding.reshape(1, -1)
                    )[0][0]
                    
                    node_data = self.graph.nodes[entity_id]
                    similarities.append({
                        'id': entity_id,
                        'similarity': float(similarity),
                        'type': node_data.get('type', ''),
                        'name': node_data.get('name', ''),
                        'description': node_data.get('description', ''),
                        'attributes': node_data.get('attributes', {})
                    })
            
            # Sort by similarity and return top results
            similarities.sort(key=lambda x: x['similarity'], reverse=True)
            return similarities[:limit]
            
        except Exception as e:
            logger.error(f"Error searching knowledge graph: {str(e)}")
            return []
    
    def get_entity(self, entity_id: str) -> Optional[Dict[str, Any]]:
        """Get entity information by ID"""
        try:
            if entity_id in self.graph:
                node_data = self.graph.nodes[entity_id]
                return {
                    'id': entity_id,
                    'type': node_data.get('type', ''),
                    'name': node_data.get('name', ''),
                    'description': node_data.get('description', ''),
                    'attributes': node_data.get('attributes', {}),
                    'relationships': self._get_entity_relationships(entity_id)
                }
            return None
        except Exception as e:
            logger.error(f"Error getting entity {entity_id}: {str(e)}")
            return None
    
    def _get_entity_relationships(self, entity_id: str) -> List[Dict[str, Any]]:
        """Get all relationships for an entity"""
        relationships = []
        
        # Outgoing relationships
        for target in self.graph.successors(entity_id):
            for edge_data in self.graph[entity_id][target].values():
                relationships.append({
                    'direction': 'outgoing',
                    'target': target,
                    'relationship': edge_data.get('relationship', ''),
                    'attributes': edge_data.get('attributes', {})
                })
        
        # Incoming relationships
        for source in self.graph.predecessors(entity_id):
            for edge_data in self.graph[source][entity_id].values():
                relationships.append({
                    'direction': 'incoming',
                    'source': source,
                    'relationship': edge_data.get('relationship', ''),
                    'attributes': edge_data.get('attributes', {})
                })
        
        return relationships
    
    def find_path(self, source_id: str, target_id: str, max_length: int = 3) -> List[List[str]]:
        """Find paths between two entities"""
        try:
            if source_id not in self.graph or target_id not in self.graph:
                return []
            
            paths = []
            for path in nx.all_simple_paths(self.graph, source_id, target_id, cutoff=max_length):
                paths.append(path)
            
            return paths[:10]  # Limit number of paths
            
        except Exception as e:
            logger.error(f"Error finding paths: {str(e)}")
            return []
    
    def get_related_entities(self, entity_id: str, relationship_type: str = None, 
                           distance: int = 1) -> List[Dict[str, Any]]:
        """Get entities related to the given entity"""
        try:
            if entity_id not in self.graph:
                return []
            
            related = []
            
            if distance == 1:
                # Direct neighbors
                neighbors = list(self.graph.successors(entity_id)) + list(self.graph.predecessors(entity_id))
                for neighbor in set(neighbors):
                    if relationship_type:
                        # Check if specific relationship exists
                        has_relationship = False
                        for edge_data in self.graph[entity_id].get(neighbor, {}).values():
                            if edge_data.get('relationship') == relationship_type:
                                has_relationship = True
                                break
                        for edge_data in self.graph.get(neighbor, {}).get(entity_id, {}).values():
                            if edge_data.get('relationship') == relationship_type:
                                has_relationship = True
                                break
                        if not has_relationship:
                            continue
                    
                    related.append(self.get_entity(neighbor))
            else:
                # Multi-hop neighbors (simplified version)
                visited = set([entity_id])
                current_level = [entity_id]
                
                for _ in range(distance):
                    next_level = []
                    for node in current_level:
                        neighbors = list(self.graph.successors(node)) + list(self.graph.predecessors(node))
                        for neighbor in neighbors:
                            if neighbor not in visited:
                                visited.add(neighbor)
                                next_level.append(neighbor)
                                if len(related) < 50:  # Limit results
                                    related.append(self.get_entity(neighbor))
                    current_level = next_level
            
            return [r for r in related if r is not None]
            
        except Exception as e:
            logger.error(f"Error getting related entities: {str(e)}")
            return []
    
    def update_from_content(self, content_items: List[Dict[str, Any]]):
        """Update knowledge graph from processed content"""
        try:
            for item in content_items:
                # Create entity for the content item
                entity_id = f"content_{hash(item.get('url', item.get('title', '')))}_{datetime.now().timestamp()}"
                
                entity = {
                    'id': entity_id,
                    'type': 'CONTENT',
                    'name': item.get('title', 'Untitled'),
                    'description': item.get('description', item.get('content', ''))[:500],
                    'attributes': {
                        'url': item.get('url', ''),
                        'content_type': item.get('type', 'webpage'),
                        'keywords': item.get('keywords', []),
                        'scraped_at': datetime.now().isoformat()
                    }
                }
                
                self.add_entity(entity)
                
                # Create relationships based on keywords and entities
                for keyword in item.get('keywords', []):
                    # Find related entities
                    related = self.search(keyword, limit=3)
                    for rel_entity in related:
                        if rel_entity['similarity'] > 0.7:
                            self.add_relationship(entity_id, 'mentions', rel_entity['id'])
            
            # Save updated graph
            self.save_graph()
            logger.info(f"Updated knowledge graph with {len(content_items)} content items")
            
        except Exception as e:
            logger.error(f"Error updating from content: {str(e)}")
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get statistics about the knowledge graph"""
        try:
            return {
                'nodes': self.graph.number_of_nodes(),
                'edges': self.graph.number_of_edges(),
                'entity_types': list(self.entity_types),
                'relationship_types': list(self.relationship_types),
                'connected_components': nx.number_weakly_connected_components(self.graph),
                'density': nx.density(self.graph) if self.graph.number_of_nodes() > 0 else 0,
                'last_updated': datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Error getting statistics: {str(e)}")
            return {}
    
    def export_to_json(self, filepath: str):
        """Export knowledge graph to JSON format"""
        try:
            data = {
                'nodes': [],
                'edges': [],
                'metadata': self.get_statistics()
            }
            
            # Export nodes
            for node_id, node_data in self.graph.nodes(data=True):
                data['nodes'].append({
                    'id': node_id,
                    **node_data
                })
            
            # Export edges
            for source, target, edge_data in self.graph.edges(data=True):
                data['edges'].append({
                    'source': source,
                    'target': target,
                    **edge_data
                })
            
            with open(filepath, 'w') as f:
                json.dump(data, f, indent=2, default=str)
            
            logger.info(f"Knowledge graph exported to {filepath}")
            
        except Exception as e:
            logger.error(f"Error exporting to JSON: {str(e)}")