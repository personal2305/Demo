// MOSDAC AI Help Bot - Chat Interface JavaScript

class ChatInterface {
    constructor() {
        this.socket = null;
        this.currentSessionId = this.generateSessionId();
        this.isTyping = false;
        this.initializeSocket();
        this.setupEventListeners();
        this.loadKnowledgeGraphStats();
    }

    generateSessionId() {
        return 'session_' + Math.random().toString(36).substr(2, 9) + '_' + Date.now();
    }

    initializeSocket() {
        this.socket = io();
        
        this.socket.on('connect', () => {
            console.log('Connected to server');
            this.updateConnectionStatus('Connected', 'success');
        });

        this.socket.on('disconnect', () => {
            console.log('Disconnected from server');
            this.updateConnectionStatus('Disconnected', 'danger');
        });

        this.socket.on('status', (data) => {
            console.log('Status:', data.msg);
            this.showToast(data.msg, 'info');
        });

        this.socket.on('bot_response', (data) => {
            this.handleBotResponse(data);
        });
    }

    setupEventListeners() {
        // Send button click
        document.getElementById('send-button').addEventListener('click', () => {
            this.sendMessage();
        });

        // Enter key press
        document.getElementById('message-input').addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });

        // Quick action buttons
        document.querySelectorAll('.quick-action').forEach(button => {
            button.addEventListener('click', (e) => {
                const query = e.target.closest('button').dataset.query;
                document.getElementById('message-input').value = query;
                this.sendMessage();
            });
        });

        // Suggestion chips (delegated event listener)
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('suggestion-chip')) {
                const query = e.target.textContent;
                document.getElementById('message-input').value = query;
                this.sendMessage();
            }
        });
    }

    sendMessage() {
        const input = document.getElementById('message-input');
        const message = input.value.trim();
        
        if (!message) return;

        // Clear input and show user message
        input.value = '';
        this.addMessage(message, 'user');
        this.showTypingIndicator();

        // Send to server
        this.socket.emit('user_message', {
            message: message,
            session_id: this.currentSessionId
        });

        // Disable input temporarily
        this.setInputState(false);
    }

    addMessage(content, sender, data = null) {
        const container = document.getElementById('messages-container');
        
        // Remove welcome message if it exists
        const welcomeMessage = container.querySelector('.welcome-message');
        if (welcomeMessage) {
            welcomeMessage.remove();
        }

        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${sender}`;

        const bubbleDiv = document.createElement('div');
        bubbleDiv.className = 'message-bubble';

        if (sender === 'bot' && data) {
            bubbleDiv.innerHTML = this.formatBotMessage(content, data);
        } else {
            bubbleDiv.textContent = content;
        }

        const infoDiv = document.createElement('div');
        infoDiv.className = 'message-info';
        infoDiv.textContent = new Date().toLocaleTimeString();

        messageDiv.appendChild(bubbleDiv);
        messageDiv.appendChild(infoDiv);

        container.appendChild(messageDiv);
        this.scrollToBottom();

        return messageDiv;
    }

    formatBotMessage(content, data) {
        let html = `<div class="message-content">${this.formatText(content)}</div>`;

        // Add confidence indicator
        if (data.confidence !== undefined) {
            const confidenceClass = this.getConfidenceClass(data.confidence);
            html += `<div class="bot-features">
                <span class="confidence-indicator ${confidenceClass}">
                    Confidence: ${(data.confidence * 100).toFixed(0)}%
                </span>
            </div>`;
        }

        // Add sources
        if (data.sources && data.sources.length > 0) {
            html += '<div class="sources-list"><strong>Sources:</strong>';
            data.sources.forEach(source => {
                html += `<div class="source-item">• ${source.title}</div>`;
            });
            html += '</div>';
        }

        // Add geospatial content
        if (data.geospatial_data && data.geospatial_data.has_spatial_data) {
            html += this.formatGeospatialContent(data.geospatial_data);
        }

        // Add suggestions
        if (data.suggestions && data.suggestions.length > 0) {
            html += '<div class="bot-features">';
            html += '<div class="suggestions-container">';
            data.suggestions.forEach(suggestion => {
                html += `<span class="suggestion-chip">${suggestion}</span>`;
            });
            html += '</div></div>';
        }

        return html;
    }

    formatText(text) {
        // Convert newlines to <br> and format basic markdown
        return text
            .replace(/\n/g, '<br>')
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\*(.*?)\*/g, '<em>$1</em>')
            .replace(/`(.*?)`/g, '<code>$1</code>');
    }

    formatGeospatialContent(geospatialData) {
        let html = '<div class="geospatial-content">';
        html += '<h6><i class="fas fa-map-marker-alt me-2"></i>Spatial Information</h6>';

        if (geospatialData.coordinates && geospatialData.coordinates.length > 0) {
            html += '<div class="coordinates-section">';
            html += '<strong>Coordinates:</strong><br>';
            geospatialData.coordinates.forEach(coord => {
                html += `<span class="coordinates-display">${coord.lat.toFixed(4)}°, ${coord.lon.toFixed(4)}°</span> `;
            });
            html += '</div>';
        }

        if (geospatialData.locations && geospatialData.locations.length > 0) {
            html += '<div class="locations-section mt-2">';
            html += '<strong>Locations:</strong> ';
            const locationNames = geospatialData.locations.map(loc => loc.name).join(', ');
            html += locationNames;
            html += '</div>';
        }

        if (geospatialData.map_data && geospatialData.map_data.has_data) {
            html += '<div class="map-section mt-2">';
            html += '<button class="btn btn-sm btn-outline-primary" onclick="showMap()">View on Map</button>';
            html += '</div>';
        }

        html += '</div>';
        return html;
    }

    getConfidenceClass(confidence) {
        if (confidence >= 0.8) return 'confidence-high';
        if (confidence >= 0.5) return 'confidence-medium';
        return 'confidence-low';
    }

    showTypingIndicator() {
        const container = document.getElementById('messages-container');
        
        const typingDiv = document.createElement('div');
        typingDiv.className = 'message bot typing-message';
        typingDiv.innerHTML = `
            <div class="typing-indicator">
                <div class="typing-dots">
                    <div class="typing-dot"></div>
                    <div class="typing-dot"></div>
                    <div class="typing-dot"></div>
                </div>
            </div>
        `;

        container.appendChild(typingDiv);
        this.scrollToBottom();
        this.isTyping = true;
    }

    hideTypingIndicator() {
        const typingMessage = document.querySelector('.typing-message');
        if (typingMessage) {
            typingMessage.remove();
        }
        this.isTyping = false;
    }

    handleBotResponse(data) {
        this.hideTypingIndicator();
        this.addMessage(data.message, 'bot', data);
        this.setInputState(true);
        
        // Update suggestions in input area
        this.updateSuggestions(data.suggestions || []);
    }

    updateSuggestions(suggestions) {
        const container = document.getElementById('suggestions-container');
        container.innerHTML = '';

        suggestions.forEach(suggestion => {
            const chip = document.createElement('span');
            chip.className = 'suggestion-chip';
            chip.textContent = suggestion;
            container.appendChild(chip);
        });
    }

    setInputState(enabled) {
        const input = document.getElementById('message-input');
        const button = document.getElementById('send-button');
        
        input.disabled = !enabled;
        button.disabled = !enabled;

        if (enabled) {
            input.focus();
        }
    }

    scrollToBottom() {
        const container = document.getElementById('messages-container');
        container.scrollTop = container.scrollHeight;
    }

    updateConnectionStatus(status, type) {
        const statusElement = document.getElementById('connection-status');
        statusElement.className = `badge bg-${type}`;
        statusElement.innerHTML = `<i class="fas fa-circle me-1"></i>${status}`;
    }

    async loadKnowledgeGraphStats() {
        try {
            const response = await fetch('/api/knowledge_graph/stats');
            const stats = await response.json();
            
            document.getElementById('entity-count').textContent = stats.nodes || 0;
            document.getElementById('relationship-count').textContent = stats.edges || 0;
        } catch (error) {
            console.error('Error loading knowledge graph stats:', error);
        }
    }

    showToast(message, type = 'info') {
        // Create toast notification
        const toast = document.createElement('div');
        toast.className = `toast align-items-center text-white bg-${type} border-0`;
        toast.setAttribute('role', 'alert');
        toast.setAttribute('aria-live', 'assertive');
        toast.setAttribute('aria-atomic', 'true');
        
        toast.innerHTML = `
            <div class="d-flex">
                <div class="toast-body">
                    ${message}
                </div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" 
                        data-bs-dismiss="toast" aria-label="Close"></button>
            </div>
        `;

        // Add to page
        let toastContainer = document.querySelector('.toast-container');
        if (!toastContainer) {
            toastContainer = document.createElement('div');
            toastContainer.className = 'toast-container position-fixed top-0 end-0 p-3';
            document.body.appendChild(toastContainer);
        }

        toastContainer.appendChild(toast);

        // Show toast
        const bsToast = new bootstrap.Toast(toast);
        bsToast.show();

        // Remove after shown
        toast.addEventListener('hidden.bs.toast', () => {
            toast.remove();
        });
    }
}

// Global functions
function clearChat() {
    const container = document.getElementById('messages-container');
    container.innerHTML = `
        <div class="welcome-message">
            <div class="card border-0 shadow-sm">
                <div class="card-body text-center">
                    <i class="fas fa-robot fa-3x text-primary mb-3"></i>
                    <h4>Welcome back!</h4>
                    <p class="text-muted">Chat cleared. How can I help you today?</p>
                </div>
            </div>
        </div>
    `;
    
    // Clear suggestions
    document.getElementById('suggestions-container').innerHTML = '';
    
    // Focus input
    document.getElementById('message-input').focus();
}

function showMap() {
    // This would show the map modal with geospatial data
    const modal = new bootstrap.Modal(document.getElementById('mapModal'));
    
    // Load map content (placeholder for now)
    document.getElementById('map-content').innerHTML = `
        <div class="d-flex align-items-center justify-content-center h-100">
            <div class="text-center">
                <i class="fas fa-map fa-3x text-muted mb-3"></i>
                <p class="text-muted">Interactive map will be displayed here</p>
                <small>Showing coordinates and spatial data from the query</small>
            </div>
        </div>
    `;
    
    modal.show();
}

// Initialize chat interface when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.chatInterface = new ChatInterface();
    
    // Focus input on load
    document.getElementById('message-input').focus();
    
    console.log('MOSDAC AI Help Bot initialized');
});