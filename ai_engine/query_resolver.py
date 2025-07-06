import logging
from typing import Dict, List, Any
import json
from datetime import datetime

logger = logging.getLogger(__name__)

class QueryResolver:
    """Main query resolver that combines all AI components to generate responses"""
    
    def __init__(self, nlp_processor, knowledge_graph, geospatial_handler):
        self.nlp_processor = nlp_processor
        self.knowledge_graph = knowledge_graph
        self.geospatial_handler = geospatial_handler
        self.session_contexts = {}  # Store conversation context per session
        
    def process_query(self, query: str, session_id: str = 'default') -> Dict[str, Any]:
        """Process a user query and return a comprehensive response"""
        try:
            logger.info(f"Processing query for session {session_id}: {query}")
            
            # Process query through NLP
            nlp_result = self.nlp_processor.process_query(query)
            
            # Handle geospatial queries
            geospatial_data = None
            if nlp_result['is_geospatial']:
                geospatial_data = self.geospatial_handler.process_geospatial_query(nlp_result)
            
            # Search knowledge graph
            kg_results = self.knowledge_graph.search(query, limit=5)
            
            # Generate response based on intent
            response = self._generate_response(nlp_result, kg_results, geospatial_data, session_id)
            
            # Update session context
            self._update_session_context(session_id, query, response)
            
            return response
            
        except Exception as e:
            logger.error(f"Error processing query: {str(e)}")
            return self._get_error_response(query)
    
    def _generate_response(self, nlp_result: Dict, kg_results: List[Dict], 
                         geospatial_data: Dict = None, session_id: str = 'default') -> Dict[str, Any]:
        """Generate a comprehensive response based on all processed data"""
        
        # Determine the primary intent
        primary_intent = max(nlp_result['intent'].items(), key=lambda x: x[1])[0]
        
        # Generate response based on intent
        if primary_intent == 'data_request':
            return self._handle_data_request(nlp_result, kg_results, geospatial_data)
        elif primary_intent == 'geospatial_query':
            return self._handle_geospatial_query(nlp_result, kg_results, geospatial_data)
        elif primary_intent == 'technical_support':
            return self._handle_technical_support(nlp_result, kg_results)
        elif primary_intent == 'navigation_help':
            return self._handle_navigation_help(nlp_result, kg_results)
        else:
            return self._handle_information_query(nlp_result, kg_results, geospatial_data)
    
    def _handle_data_request(self, nlp_result: Dict, kg_results: List[Dict], 
                           geospatial_data: Dict = None) -> Dict[str, Any]:
        """Handle data download/access requests"""
        
        response_text = "I can help you access satellite data from MOSDAC. "
        suggestions = []
        sources = []
        
        # Check for specific satellites or data products in entities
        satellites = [e['text'] for e in nlp_result['entities'] if e['label'] == 'SATELLITE']
        products = [e['text'] for e in nlp_result['entities'] if e['label'] == 'PRODUCT']
        
        if satellites:
            response_text += f"I found that you're interested in {', '.join(satellites)} data. "
            suggestions.extend([
                f"Browse {satellites[0]} data products",
                f"Check {satellites[0]} data availability",
                "View data download guidelines"
            ])
        
        if products:
            response_text += f"For {', '.join(products)} products, "
            suggestions.extend([
                f"Download {products[0]} data",
                f"Learn about {products[0]} specifications",
                "View product documentation"
            ])
        
        if geospatial_data and geospatial_data['has_spatial_data']:
            response_text += "I can see you've specified a location. "
            if geospatial_data['coordinates']:
                coord = geospatial_data['coordinates'][0]
                response_text += f"For coordinates {coord['lat']:.2f}, {coord['lon']:.2f}, "
            suggestions.extend([
                "View data coverage for your area",
                "Check spatial resolution options",
                "Download regional data subset"
            ])
        
        # Add relevant knowledge graph results
        if kg_results:
            response_text += "Here are some relevant data sources I found:\n"
            for result in kg_results[:3]:
                response_text += f"• {result['name']}: {result['description'][:100]}...\n"
                sources.append({
                    'title': result['name'],
                    'description': result['description'],
                    'type': result['type'],
                    'relevance': result['similarity']
                })
        
        response_text += "\n\nTo access data:\n"
        response_text += "1. Register on the MOSDAC portal\n"
        response_text += "2. Browse the data catalog\n"
        response_text += "3. Select your area of interest\n"
        response_text += "4. Choose data products and download\n"
        
        return {
            'answer': response_text,
            'confidence': min(nlp_result['confidence'] + 0.2, 1.0),
            'sources': sources,
            'suggestions': suggestions[:5],
            'geospatial_data': geospatial_data
        }
    
    def _handle_geospatial_query(self, nlp_result: Dict, kg_results: List[Dict], 
                               geospatial_data: Dict) -> Dict[str, Any]:
        """Handle geospatial-specific queries"""
        
        response_text = "I can help you with spatial data queries. "
        suggestions = []
        sources = []
        
        if geospatial_data and geospatial_data['has_spatial_data']:
            spatial_context = self.geospatial_handler.generate_spatial_context(nlp_result)
            response_text += spatial_context + "\n\n"
            
            if geospatial_data['coordinates']:
                coords = geospatial_data['coordinates']
                response_text += f"Found {len(coords)} coordinate location(s). "
                for coord in coords[:2]:  # Limit to first 2 coordinates
                    response_text += f"Location: {coord['lat']:.4f}°, {coord['lon']:.4f}° "
            
            if geospatial_data['locations']:
                locations = [loc['name'] for loc in geospatial_data['locations']]
                response_text += f"Identified locations: {', '.join(locations[:3])}. "
            
            # Get data coverage information
            coverage_info = self.geospatial_handler.get_data_coverage_info(geospatial_data)
            if coverage_info:
                response_text += "\n\nAvailable satellite data for this area:\n"
                response_text += f"• Satellites: {', '.join(coverage_info.get('satellites_available', [])[:4])}\n"
                response_text += f"• Data products: {', '.join(coverage_info.get('data_products', [])[:4])}\n"
                response_text += f"• Temporal coverage: {coverage_info.get('temporal_coverage', 'Various')}\n"
                
                if 'recommended_products' in coverage_info:
                    response_text += f"\nRecommended products: {', '.join(coverage_info['recommended_products'][:3])}"
            
            suggestions.extend(geospatial_data.get('suggestions', []))
        else:
            response_text += "I didn't detect specific coordinates or location names in your query. "
            response_text += "Please provide coordinates (e.g., 28.6, 77.2) or location names (e.g., Delhi, Mumbai) "
            response_text += "for more specific spatial information."
            
            suggestions.extend([
                "Specify coordinates or location name",
                "Browse data by region",
                "Use the interactive map"
            ])
        
        # Add knowledge graph results
        for result in kg_results[:2]:
            sources.append({
                'title': result['name'],
                'description': result['description'],
                'type': result['type'],
                'relevance': result['similarity']
            })
        
        return {
            'answer': response_text,
            'confidence': nlp_result['confidence'],
            'sources': sources,
            'suggestions': suggestions[:5],
            'geospatial_data': geospatial_data
        }
    
    def _handle_technical_support(self, nlp_result: Dict, kg_results: List[Dict]) -> Dict[str, Any]:
        """Handle technical support queries"""
        
        response_text = "I'm here to help with technical issues. "
        suggestions = []
        sources = []
        
        # Check for specific technical terms
        keywords = nlp_result['keywords']
        tech_issues = ['error', 'problem', 'not working', 'download', 'access', 'login']
        
        found_issues = [issue for issue in tech_issues if any(issue in keyword for keyword in keywords)]
        
        if 'error' in keywords or 'problem' in keywords:
            response_text += "For error troubleshooting:\n"
            response_text += "1. Check your internet connection\n"
            response_text += "2. Clear browser cache and cookies\n"
            response_text += "3. Try using a different browser\n"
            response_text += "4. Ensure you're logged in to your MOSDAC account\n\n"
            
            suggestions.extend([
                "Contact technical support",
                "Check system requirements",
                "View troubleshooting guide",
                "Submit error report"
            ])
        
        if 'download' in keywords:
            response_text += "For download issues:\n"
            response_text += "• Ensure you have sufficient storage space\n"
            response_text += "• Check file size limits\n"
            response_text += "• Verify data access permissions\n"
            response_text += "• Use download manager for large files\n\n"
            
            suggestions.extend([
                "Check download guidelines",
                "Verify account permissions",
                "Use alternative download method"
            ])
        
        if 'login' in keywords or 'access' in keywords:
            response_text += "For access issues:\n"
            response_text += "• Verify your username and password\n"
            response_text += "• Check if your account is active\n"
            response_text += "• Reset password if needed\n"
            response_text += "• Contact admin for account issues\n\n"
            
            suggestions.extend([
                "Reset password",
                "Register new account",
                "Contact support team"
            ])
        
        response_text += "If the issue persists, please contact our support team with specific error details."
        
        return {
            'answer': response_text,
            'confidence': 0.8,
            'sources': sources,
            'suggestions': suggestions[:5],
            'geospatial_data': None
        }
    
    def _handle_navigation_help(self, nlp_result: Dict, kg_results: List[Dict]) -> Dict[str, Any]:
        """Handle navigation and portal usage queries"""
        
        response_text = "I can help you navigate the MOSDAC portal. "
        suggestions = []
        sources = []
        
        navigation_map = {
            'data catalog': 'Browse the data catalog section to find available datasets',
            'download': 'Use the download section to access data files',
            'user registration': 'Register in the user section to access premium features',
            'documentation': 'Check the documentation section for detailed guides',
            'faq': 'Visit the FAQ section for common questions and answers',
            'contact': 'Use the contact section to reach support team'
        }
        
        keywords = nlp_result['keywords']
        found_sections = []
        
        for section, description in navigation_map.items():
            if any(word in section for word in keywords):
                found_sections.append((section, description))
        
        if found_sections:
            response_text += "Here's how to find what you're looking for:\n\n"
            for section, description in found_sections:
                response_text += f"• {section.title()}: {description}\n"
        else:
            response_text += "Here are the main sections of the MOSDAC portal:\n\n"
            response_text += "• Data Catalog: Browse available satellite datasets\n"
            response_text += "• Download Center: Access and download data\n"
            response_text += "• User Dashboard: Manage your account and downloads\n"
            response_text += "• Documentation: Guides and technical specifications\n"
            response_text += "• Support: FAQ and contact information\n"
        
        suggestions.extend([
            "Browse data catalog",
            "View user guide",
            "Check FAQ section",
            "Access download center",
            "Visit documentation"
        ])
        
        return {
            'answer': response_text,
            'confidence': 0.9,
            'sources': sources,
            'suggestions': suggestions[:5],
            'geospatial_data': None
        }
    
    def _handle_information_query(self, nlp_result: Dict, kg_results: List[Dict], 
                                geospatial_data: Dict = None) -> Dict[str, Any]:
        """Handle general information queries"""
        
        response_text = ""
        suggestions = []
        sources = []
        
        # Use knowledge graph results as primary information source
        if kg_results:
            best_match = kg_results[0]
            if best_match['similarity'] > 0.3:
                response_text += f"Based on your query about '{nlp_result['original_query']}', "
                response_text += f"here's what I found:\n\n"
                response_text += f"{best_match['name']}: {best_match['description']}\n\n"
                
                if best_match.get('attributes'):
                    response_text += "Additional details:\n"
                    for key, value in best_match['attributes'].items():
                        if isinstance(value, (str, int, float)):
                            response_text += f"• {key.replace('_', ' ').title()}: {value}\n"
                
                sources.append({
                    'title': best_match['name'],
                    'description': best_match['description'],
                    'type': best_match['type'],
                    'relevance': best_match['similarity']
                })
                
                # Get related entities
                related_entities = self.knowledge_graph.get_related_entities(best_match['id'], distance=1)
                if related_entities:
                    response_text += f"\nRelated information:\n"
                    for entity in related_entities[:3]:
                        response_text += f"• {entity['name']}: {entity['description'][:100]}...\n"
            else:
                response_text = self._get_general_mosdac_info()
        else:
            response_text = self._get_general_mosdac_info()
        
        # Add geospatial context if relevant
        if geospatial_data and geospatial_data['has_spatial_data']:
            spatial_context = self.geospatial_handler.generate_spatial_context(nlp_result)
            response_text += f"\n\nSpatial context: {spatial_context}"
        
        # Generate suggestions based on entities and keywords
        entities = nlp_result['entities']
        keywords = nlp_result['keywords']
        
        if entities:
            for entity in entities[:2]:
                suggestions.append(f"Learn more about {entity['text']}")
        
        if keywords:
            for keyword in keywords[:3]:
                suggestions.append(f"Search for {keyword} data")
        
        suggestions.extend([
            "Browse data catalog",
            "View satellite missions",
            "Check data products",
            "Access documentation"
        ])
        
        return {
            'answer': response_text,
            'confidence': nlp_result['confidence'],
            'sources': sources,
            'suggestions': suggestions[:5],
            'geospatial_data': geospatial_data
        }
    
    def _get_general_mosdac_info(self) -> str:
        """Return general information about MOSDAC"""
        return """MOSDAC (Meteorological and Oceanographic Satellite Data Archival Centre) is India's premier satellite data repository managed by ISRO. 

Key features:
• Comprehensive satellite data archive from Indian and international satellites
• Ocean color, meteorological, and land observation data
• Real-time and historical datasets
• User-friendly data discovery and download interface
• Support for various data formats and processing levels

Available satellites include Oceansat, ResourceSat, INSAT, Cartosat, and international missions like Landsat and Sentinel.

The portal provides free access to most datasets after user registration, with advanced features for research and operational users."""
    
    def _get_error_response(self, query: str) -> Dict[str, Any]:
        """Return error response for failed query processing"""
        return {
            'answer': "I encountered an error processing your query. Please try rephrasing your question or contact support if the issue persists.",
            'confidence': 0.0,
            'sources': [],
            'suggestions': [
                "Try rephrasing your question",
                "Check spelling and grammar",
                "Contact technical support",
                "Browse FAQ section"
            ],
            'geospatial_data': None
        }
    
    def _update_session_context(self, session_id: str, query: str, response: Dict[str, Any]):
        """Update conversation context for the session"""
        if session_id not in self.session_contexts:
            self.session_contexts[session_id] = {
                'queries': [],
                'last_updated': datetime.now(),
                'topics': set()
            }
        
        context = self.session_contexts[session_id]
        context['queries'].append({
            'query': query,
            'response': response,
            'timestamp': datetime.now()
        })
        
        # Keep only last 10 queries
        if len(context['queries']) > 10:
            context['queries'] = context['queries'][-10:]
        
        context['last_updated'] = datetime.now()
    
    def get_session_context(self, session_id: str) -> Dict[str, Any]:
        """Get conversation context for a session"""
        return self.session_contexts.get(session_id, {
            'queries': [],
            'last_updated': None,
            'topics': set()
        })