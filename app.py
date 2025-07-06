from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit
from flask_cors import CORS
import os
import json
import logging
from datetime import datetime

# Import our custom modules
from ai_engine.nlp_processor import NLPProcessor
from ai_engine.knowledge_graph import KnowledgeGraph
from ai_engine.geospatial_handler import GeospatialHandler
from ai_engine.query_resolver import QueryResolver
from data_ingestion.web_scraper import WebScraper
from data_ingestion.content_processor import ContentProcessor

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-change-this'
socketio = SocketIO(app, cors_allowed_origins="*")
CORS(app)

# Initialize AI components
nlp_processor = NLPProcessor()
knowledge_graph = KnowledgeGraph()
geospatial_handler = GeospatialHandler()
query_resolver = QueryResolver(nlp_processor, knowledge_graph, geospatial_handler)
web_scraper = WebScraper()
content_processor = ContentProcessor()

@app.route('/')
def index():
    """Serve the main chat interface"""
    return render_template('index.html')

@app.route('/admin')
def admin():
    """Admin interface for managing the knowledge graph"""
    return render_template('admin.html')

@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    logger.info('Client connected')
    emit('status', {'msg': 'Connected to MOSDAC AI Help Bot'})

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    logger.info('Client disconnected')

@socketio.on('user_message')
def handle_message(data):
    """Handle incoming user messages and process them through AI engine"""
    try:
        user_message = data['message']
        session_id = data.get('session_id', 'default')
        
        logger.info(f"Processing message: {user_message}")
        
        # Process the query through our AI engine
        response = query_resolver.process_query(user_message, session_id)
        
        # Send response back to client
        emit('bot_response', {
            'message': response['answer'],
            'confidence': response['confidence'],
            'sources': response['sources'],
            'suggestions': response['suggestions'],
            'geospatial_data': response.get('geospatial_data'),
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error processing message: {str(e)}")
        emit('bot_response', {
            'message': 'Sorry, I encountered an error processing your query. Please try again.',
            'confidence': 0.0,
            'sources': [],
            'suggestions': [],
            'timestamp': datetime.now().isoformat()
        })

@app.route('/api/scrape_portal', methods=['POST'])
def scrape_portal():
    """API endpoint to scrape and process portal content"""
    try:
        data = request.json
        url = data.get('url', 'https://www.mosdac.gov.in')
        
        # Scrape the portal
        scraped_data = web_scraper.scrape_website(url)
        
        # Process the content
        processed_content = content_processor.process_content(scraped_data)
        
        # Update knowledge graph
        knowledge_graph.update_from_content(processed_content)
        
        return jsonify({
            'status': 'success',
            'message': f'Successfully processed {len(processed_content)} content items',
            'content_count': len(processed_content)
        })
        
    except Exception as e:
        logger.error(f"Error scraping portal: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/knowledge_graph/stats', methods=['GET'])
def get_kg_stats():
    """Get knowledge graph statistics"""
    try:
        stats = knowledge_graph.get_statistics()
        return jsonify(stats)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/search', methods=['POST'])
def search_knowledge():
    """Search the knowledge graph directly"""
    try:
        data = request.json
        query = data.get('query', '')
        limit = data.get('limit', 10)
        
        results = knowledge_graph.search(query, limit)
        
        return jsonify({
            'status': 'success',
            'results': results
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

if __name__ == '__main__':
    # Initialize the system
    logger.info("Starting MOSDAC AI Help Bot...")
    
    # Create necessary directories
    os.makedirs('data', exist_ok=True)
    os.makedirs('models', exist_ok=True)
    os.makedirs('logs', exist_ok=True)
    
    # Start the application
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)