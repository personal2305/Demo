# MOSDAC AI Help Bot

An intelligent conversational assistant for satellite data retrieval and information access from the MOSDAC (Meteorological and Oceanographic Satellite Data Archival Centre) portal.

## 🚀 Features

### Core Capabilities
- **Natural Language Processing**: Advanced query understanding with entity extraction and intent classification
- **Knowledge Graph**: Dynamic graph-based information storage and retrieval
- **Geospatial Intelligence**: Location-aware query processing with coordinate extraction and mapping
- **Real-time Chat Interface**: Modern, responsive web interface with real-time messaging
- **Contextual Responses**: AI-powered responses with confidence scoring and source attribution
- **Multi-modal Support**: Text, geospatial data, and interactive map visualizations

### Specialized Features
- **Satellite Data Expertise**: Domain-specific knowledge about MOSDAC satellites (Oceansat, ResourceSat, INSAT, etc.)
- **Data Product Intelligence**: Information about various satellite data products (NDVI, SST, Ocean Color, etc.)
- **Download Assistance**: Step-by-step guidance for data access and download procedures
- **Technical Support**: Troubleshooting help for common portal issues
- **Portal Navigation**: Interactive guidance through MOSDAC interface

### Admin Features
- **Knowledge Graph Management**: Browse, search, and manage the knowledge base
- **Data Ingestion Pipeline**: Automated web scraping and content processing
- **System Monitoring**: Real-time statistics and performance monitoring
- **Modular Architecture**: Easy deployment to other similar portals

## 🏗️ Architecture

### AI Engine Components
- **NLP Processor**: spaCy + Transformers for query understanding
- **Knowledge Graph**: NetworkX-based graph storage with semantic search
- **Geospatial Handler**: Coordinate extraction and spatial query processing
- **Query Resolver**: Intent-based response generation

### Data Pipeline
- **Web Scraper**: Respectful crawling of portal content
- **Content Processor**: Text extraction and entity recognition
- **Knowledge Graph Integration**: Automated graph updates

### Frontend
- **Modern UI**: Bootstrap 5 + custom CSS with responsive design
- **Real-time Communication**: Socket.IO for instant messaging
- **Interactive Features**: Quick actions, suggestions, and geospatial visualization

## 🛠️ Installation

### Prerequisites
- Python 3.8+
- pip package manager
- Internet connection for downloading models

### Quick Start

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd mosdac-ai-helpbot
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Download NLP models**
   ```bash
   python -m spacy download en_core_web_sm
   ```

4. **Run the application**
   ```bash
   python app.py
   ```

5. **Access the interfaces**
   - Chat Interface: http://localhost:5000
   - Admin Panel: http://localhost:5000/admin

### Advanced Setup

#### Environment Configuration
Create a `.env` file for configuration:
```bash
FLASK_SECRET_KEY=your-secret-key-here
KNOWLEDGE_GRAPH_PATH=data/knowledge_graph.pkl
LOG_LEVEL=INFO
```

#### Production Deployment
For production deployment:
```bash
# Install production WSGI server
pip install gunicorn

# Run with gunicorn
gunicorn --worker-class eventlet -w 1 app:app --bind 0.0.0.0:5000
```

## 📖 Usage Guide

### Chat Interface

#### Basic Queries
- **Data Requests**: "How to download Oceansat data?"
- **Information Queries**: "What is sea surface temperature?"
- **Navigation Help**: "How to access the data catalog?"
- **Technical Support**: "Getting download errors"

#### Geospatial Queries
- **Coordinate-based**: "Show data for 28.6, 77.2"
- **Location-based**: "Satellite data for Mumbai"
- **Coverage queries**: "What satellites cover Indian Ocean?"

#### Advanced Features
- **Quick Actions**: Use sidebar buttons for common queries
- **Suggestions**: Click on suggested follow-up questions
- **Sources**: View information sources and confidence scores
- **Maps**: Interactive visualization for geospatial queries

### Admin Interface

#### Dashboard
- Monitor system statistics and performance
- View knowledge graph metrics
- Track recent activity and system health

#### Knowledge Graph Management
- Search and browse entities and relationships
- View graph statistics and structure
- Export knowledge graph data

#### Data Ingestion
- Scrape new content from web portals
- Process and integrate content into knowledge graph
- Monitor scraping progress and results

#### System Monitoring
- View application logs
- Monitor system performance
- Troubleshoot issues

## 🔧 Configuration

### NLP Configuration
Modify `ai_engine/nlp_processor.py` to:
- Add domain-specific entity patterns
- Customize intent classification rules
- Adjust confidence thresholds

### Knowledge Graph Customization
Edit `ai_engine/knowledge_graph.py` to:
- Define custom entity types
- Add relationship categories
- Modify search algorithms

### Geospatial Settings
Configure `ai_engine/geospatial_handler.py` for:
- Custom coordinate patterns
- Location recognition rules
- Map visualization preferences

### Web Scraping Rules
Adjust `data_ingestion/web_scraper.py` for:
- Crawling policies and delays
- Content extraction rules
- Site-specific adaptations

## 🎯 Query Examples

### Data Access Queries
```
"How do I download Oceansat chlorophyll data?"
"What's the procedure to access INSAT meteorological data?"
"Show me available ResourceSat land data products"
```

### Information Queries
```
"What is NDVI and how is it calculated?"
"Explain sea surface temperature measurements"
"Tell me about Oceansat satellite sensors"
```

### Geospatial Queries
```
"Show satellite coverage for coordinates 15.5, 73.8"
"What data is available for the Arabian Sea?"
"Find datasets covering Karnataka state"
```

### Technical Support
```
"I'm getting a download error, what should I do?"
"How to register for data access?"
"The portal is not loading properly"
```

## 🔮 Extension Possibilities

### Portal Integration
- **Multi-portal Support**: Extend to other satellite data portals
- **API Integration**: Direct integration with data APIs
- **Single Sign-On**: User authentication integration

### Advanced AI Features
- **Voice Interface**: Speech-to-text and text-to-speech
- **Multi-language Support**: Regional language processing
- **Predictive Suggestions**: ML-based query prediction

### Data Enhancement
- **Real-time Data**: Integration with live satellite feeds
- **Advanced Analytics**: Trend analysis and recommendations
- **Custom Dashboards**: User-specific data views

### Visualization Improvements
- **3D Mapping**: Advanced geospatial visualization
- **Time Series**: Temporal data exploration
- **Interactive Charts**: Dynamic data visualization

## 🤝 Contributing

### Development Setup
1. Fork the repository
2. Create a feature branch
3. Make changes with proper testing
4. Submit a pull request

### Code Style
- Follow PEP 8 for Python code
- Use meaningful variable and function names
- Add docstrings for all classes and functions
- Include type hints where appropriate

### Testing
```bash
# Run unit tests
python -m pytest tests/

# Run integration tests
python -m pytest tests/integration/

# Check code coverage
python -m pytest --cov=.
```

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- **ISRO/MOSDAC**: For providing satellite data and portal access
- **spaCy**: For natural language processing capabilities
- **NetworkX**: For graph-based knowledge representation
- **Flask**: For web application framework
- **Bootstrap**: For responsive UI components

## 📞 Support

For issues, questions, or contributions:
- Open an issue on GitHub
- Check the documentation in the `docs/` folder
- Review the FAQ section in the admin interface

---

**MOSDAC AI Help Bot** - Making satellite data accessible through intelligent conversation.