#!/usr/bin/env python3
"""
MOSDAC AI Help Bot - System Test Script
Demonstrates the capabilities of the AI engine components
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from ai_engine.nlp_processor import NLPProcessor
from ai_engine.knowledge_graph import KnowledgeGraph
from ai_engine.geospatial_handler import GeospatialHandler
from ai_engine.query_resolver import QueryResolver

def test_nlp_processor():
    """Test the NLP processor capabilities"""
    print("🧠 Testing NLP Processor...")
    print("-" * 40)
    
    nlp = NLPProcessor()
    
    test_queries = [
        "How do I download Oceansat chlorophyll data for Mumbai?",
        "What satellites are available for ocean temperature data?",
        "I'm getting an error when accessing the data portal",
        "Show me NDVI data for coordinates 28.6, 77.2"
    ]
    
    for query in test_queries:
        print(f"\nQuery: {query}")
        result = nlp.process_query(query)
        print(f"Intent: {max(result['intent'].items(), key=lambda x: x[1])}")
        print(f"Entities: {[e['text'] for e in result['entities']]}")
        print(f"Keywords: {result['keywords'][:5]}")
        print(f"Geospatial: {result['is_geospatial']}")
        print(f"Confidence: {result['confidence']:.2f}")

def test_knowledge_graph():
    """Test the knowledge graph functionality"""
    print("\n\n📊 Testing Knowledge Graph...")
    print("-" * 40)
    
    kg = KnowledgeGraph()
    
    # Search for different terms
    test_searches = ["oceansat", "satellite data", "ocean color", "MOSDAC"]
    
    for search_term in test_searches:
        print(f"\nSearching for: {search_term}")
        results = kg.search(search_term, limit=3)
        for result in results:
            print(f"  - {result['name']} ({result['type']}) - {result['similarity']:.3f}")
    
    # Display statistics
    stats = kg.get_statistics()
    print(f"\nKnowledge Graph Stats:")
    print(f"  - Nodes: {stats['nodes']}")
    print(f"  - Edges: {stats['edges']}")
    print(f"  - Entity Types: {stats['entity_types']}")

def test_geospatial_handler():
    """Test the geospatial processing capabilities"""
    print("\n\n🗺️  Testing Geospatial Handler...")
    print("-" * 40)
    
    geo = GeospatialHandler()
    
    test_queries = [
        "Show data for coordinates 28.6, 77.2",
        "I need satellite data for Mumbai region",
        "What's available for the Arabian Sea area?",
        "Coverage data for 15.5°N, 73.8°E location"
    ]
    
    for query in test_queries:
        print(f"\nQuery: {query}")
        
        # Mock query data
        query_data = {'cleaned_query': query.lower()}
        result = geo.process_geospatial_query(query_data)
        
        print(f"  - Coordinates found: {len(result['coordinates'])}")
        print(f"  - Locations found: {len(result['locations'])}")
        print(f"  - Spatial intent: {result['spatial_intent']}")
        print(f"  - Has spatial data: {result['has_spatial_data']}")

def test_query_resolver():
    """Test the complete query resolution system"""
    print("\n\n🎯 Testing Query Resolver...")
    print("-" * 40)
    
    # Initialize components
    nlp = NLPProcessor()
    kg = KnowledgeGraph()
    geo = GeospatialHandler()
    resolver = QueryResolver(nlp, kg, geo)
    
    test_queries = [
        "How to download Oceansat data?",
        "What is sea surface temperature?",
        "Show satellite data for Delhi",
        "I'm having trouble accessing the portal"
    ]
    
    for query in test_queries:
        print(f"\nQuery: {query}")
        response = resolver.process_query(query)
        
        print(f"Answer: {response['answer'][:150]}...")
        print(f"Confidence: {response['confidence']:.2f}")
        print(f"Sources: {len(response['sources'])}")
        print(f"Suggestions: {response['suggestions'][:2]}")

def run_interactive_demo():
    """Run an interactive demo"""
    print("\n\n🎮 Interactive Demo")
    print("-" * 40)
    print("Enter queries to test the AI system (type 'quit' to exit):")
    
    # Initialize the complete system
    nlp = NLPProcessor()
    kg = KnowledgeGraph()
    geo = GeospatialHandler()
    resolver = QueryResolver(nlp, kg, geo)
    
    while True:
        try:
            query = input("\n🗣️  Your query: ").strip()
            
            if query.lower() in ['quit', 'exit', 'q']:
                break
            
            if not query:
                continue
            
            print("\n🤖 Processing...")
            response = resolver.process_query(query)
            
            print(f"\n💬 Response:")
            print(response['answer'])
            
            if response['suggestions']:
                print(f"\n💡 Suggestions:")
                for suggestion in response['suggestions'][:3]:
                    print(f"  - {suggestion}")
            
            print(f"\n📊 Confidence: {response['confidence']:.1%}")
            
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"❌ Error: {e}")
    
    print("\n👋 Demo ended!")

def main():
    """Main test function"""
    print("🚀 MOSDAC AI Help Bot - System Tests")
    print("=" * 50)
    
    try:
        test_nlp_processor()
        test_knowledge_graph()
        test_geospatial_handler()
        test_query_resolver()
        
        print("\n\n✅ All tests completed successfully!")
        
        # Ask if user wants interactive demo
        response = input("\n🎮 Would you like to try the interactive demo? (y/n): ")
        if response.lower().startswith('y'):
            run_interactive_demo()
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()