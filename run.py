#!/usr/bin/env python3
"""
MOSDAC AI Help Bot - Startup Script
Simple script to launch the application with proper configuration
"""

import os
import sys
import logging
from pathlib import Path

def check_dependencies():
    """Check if all required dependencies are installed"""
    try:
        import flask
        import flask_socketio
        import spacy
        import transformers
        import networkx
        import beautifulsoup4
        import folium
        print("✓ All core dependencies found")
        return True
    except ImportError as e:
        print(f"✗ Missing dependency: {e}")
        print("Please run: pip install -r requirements.txt")
        return False

def check_nlp_models():
    """Check if required NLP models are available"""
    try:
        import spacy
        nlp = spacy.load("en_core_web_sm")
        print("✓ spaCy English model found")
        return True
    except OSError:
        print("✗ spaCy English model not found")
        print("Please run: python -m spacy download en_core_web_sm")
        return False

def setup_directories():
    """Create necessary directories"""
    directories = ['data', 'models', 'logs']
    
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
        print(f"✓ Directory '{directory}' ready")

def setup_environment():
    """Setup environment variables"""
    if not os.getenv('FLASK_SECRET_KEY'):
        os.environ['FLASK_SECRET_KEY'] = 'dev-secret-key-change-in-production'
    
    # Set log level
    if not os.getenv('LOG_LEVEL'):
        os.environ['LOG_LEVEL'] = 'INFO'
    
    print("✓ Environment configured")

def main():
    """Main startup function"""
    print("🚀 Starting MOSDAC AI Help Bot...")
    print("=" * 50)
    
    # Check system requirements
    if not check_dependencies():
        sys.exit(1)
    
    if not check_nlp_models():
        print("\nAttempting to download spaCy model...")
        os.system("python -m spacy download en_core_web_sm")
    
    # Setup application
    setup_directories()
    setup_environment()
    
    print("\n" + "=" * 50)
    print("🎯 Launching application...")
    print("📱 Chat Interface: http://localhost:5000")
    print("⚙️  Admin Panel: http://localhost:5000/admin")
    print("=" * 50)
    
    # Import and run the Flask app
    try:
        from app import app, socketio
        
        # Configure logging
        log_level = getattr(logging, os.getenv('LOG_LEVEL', 'INFO'))
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # Start the application
        socketio.run(
            app, 
            debug=True, 
            host='0.0.0.0', 
            port=5000,
            allow_unsafe_werkzeug=True
        )
        
    except KeyboardInterrupt:
        print("\n\n👋 Shutting down gracefully...")
    except Exception as e:
        print(f"\n❌ Error starting application: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()