// MOSDAC AI Help Bot - Admin Interface JavaScript

class AdminInterface {
    constructor() {
        this.currentSection = 'dashboard';
        this.loadingOverlay = null;
        this.initializeAdmin();
    }

    initializeAdmin() {
        this.loadDashboardData();
        this.setupEventListeners();
        console.log('Admin interface initialized');
    }

    setupEventListeners() {
        // Section navigation
        document.querySelectorAll('.list-group-item').forEach(item => {
            item.addEventListener('click', (e) => {
                e.preventDefault();
                const href = item.getAttribute('href');
                if (href && href.startsWith('#')) {
                    const sectionName = href.substring(1);
                    this.showSection(sectionName);
                }
            });
        });

        // Knowledge graph search
        const kgSearchInput = document.getElementById('kg-search-input');
        if (kgSearchInput) {
            kgSearchInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') {
                    this.searchKnowledgeGraph();
                }
            });
        }

        // Portal URL input
        const portalUrlInput = document.getElementById('portal-url');
        if (portalUrlInput) {
            portalUrlInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') {
                    this.scrapePortal();
                }
            });
        }
    }

    showSection(sectionName) {
        // Hide all sections
        document.querySelectorAll('.content-section').forEach(section => {
            section.style.display = 'none';
        });

        // Show selected section
        const selectedSection = document.getElementById(`${sectionName}-section`);
        if (selectedSection) {
            selectedSection.style.display = 'block';
        }

        // Update navigation
        document.querySelectorAll('.list-group-item').forEach(item => {
            item.classList.remove('active');
        });
        
        const activeItem = document.querySelector(`[href="#${sectionName}"]`);
        if (activeItem) {
            activeItem.classList.add('active');
        }

        this.currentSection = sectionName;

        // Load section-specific data
        this.loadSectionData(sectionName);
    }

    loadSectionData(sectionName) {
        switch (sectionName) {
            case 'dashboard':
                this.loadDashboardData();
                break;
            case 'knowledge-graph':
                this.loadKnowledgeGraphData();
                break;
            case 'data-ingestion':
                // Data ingestion section doesn't need initial loading
                break;
            case 'system-logs':
                this.loadSystemLogs();
                break;
        }
    }

    async loadDashboardData() {
        try {
            this.showLoading();
            
            // Load knowledge graph statistics
            const kgStats = await this.fetchKnowledgeGraphStats();
            this.updateDashboardStats(kgStats);
            
            // Load recent activity
            this.loadRecentActivity();
            
            // Load entity types chart
            this.loadEntityTypesChart(kgStats);
            
        } catch (error) {
            console.error('Error loading dashboard data:', error);
            this.showError('Failed to load dashboard data');
        } finally {
            this.hideLoading();
        }
    }

    async fetchKnowledgeGraphStats() {
        const response = await fetch('/api/knowledge_graph/stats');
        if (!response.ok) {
            throw new Error('Failed to fetch knowledge graph stats');
        }
        return await response.json();
    }

    updateDashboardStats(stats) {
        document.getElementById('total-entities').textContent = stats.nodes || 0;
        document.getElementById('total-relationships').textContent = stats.edges || 0;
        
        // Mock data for queries today and system health
        document.getElementById('queries-today').textContent = Math.floor(Math.random() * 150) + 50;
        document.getElementById('system-health').textContent = 'Good';
    }

    loadRecentActivity() {
        const activityContainer = document.getElementById('recent-activity');
        const activities = [
            {
                icon: 'fas fa-plus',
                type: 'success',
                title: 'New entity added',
                time: '2 minutes ago'
            },
            {
                icon: 'fas fa-search',
                type: 'info',
                title: 'Knowledge graph searched',
                time: '5 minutes ago'
            },
            {
                icon: 'fas fa-download',
                type: 'success',
                title: 'Portal content scraped',
                time: '1 hour ago'
            },
            {
                icon: 'fas fa-exclamation-triangle',
                type: 'warning',
                title: 'Low confidence query detected',
                time: '2 hours ago'
            }
        ];

        let html = '';
        activities.forEach(activity => {
            html += `
                <div class="activity-item">
                    <div class="activity-icon ${activity.type}">
                        <i class="${activity.icon}"></i>
                    </div>
                    <div class="activity-content">
                        <div class="activity-title">${activity.title}</div>
                        <div class="activity-time">${activity.time}</div>
                    </div>
                </div>
            `;
        });

        activityContainer.innerHTML = html;
    }

    loadEntityTypesChart(stats) {
        const chartContainer = document.getElementById('entity-types-chart');
        
        if (stats.entity_types && stats.entity_types.length > 0) {
            // Create a simple bar chart representation
            let html = '<div class="entity-types-bars">';
            
            stats.entity_types.forEach((type, index) => {
                const percentage = Math.random() * 80 + 20; // Mock percentage
                const colors = ['#3498db', '#27ae60', '#f39c12', '#e74c3c', '#9b59b6'];
                const color = colors[index % colors.length];
                
                html += `
                    <div class="chart-bar mb-3">
                        <div class="d-flex justify-content-between align-items-center mb-1">
                            <span class="chart-label">${type}</span>
                            <span class="chart-value">${percentage.toFixed(0)}%</span>
                        </div>
                        <div class="progress" style="height: 8px;">
                            <div class="progress-bar" style="width: ${percentage}%; background-color: ${color};"></div>
                        </div>
                    </div>
                `;
            });
            
            html += '</div>';
            chartContainer.innerHTML = html;
        } else {
            chartContainer.innerHTML = '<div class="chart-placeholder">No entity types data available</div>';
        }
    }

    async loadKnowledgeGraphData() {
        try {
            const stats = await this.fetchKnowledgeGraphStats();
            this.updateKnowledgeGraphStats(stats);
        } catch (error) {
            console.error('Error loading knowledge graph data:', error);
        }
    }

    updateKnowledgeGraphStats(stats) {
        const statsTable = document.getElementById('kg-stats-table');
        let html = '';
        
        const statsData = [
            { label: 'Total Nodes', value: stats.nodes || 0 },
            { label: 'Total Edges', value: stats.edges || 0 },
            { label: 'Entity Types', value: stats.entity_types ? stats.entity_types.length : 0 },
            { label: 'Relationship Types', value: stats.relationship_types ? stats.relationship_types.length : 0 },
            { label: 'Connected Components', value: stats.connected_components || 0 },
            { label: 'Graph Density', value: stats.density ? stats.density.toFixed(4) : '0.0000' }
        ];

        statsData.forEach(stat => {
            html += `
                <tr>
                    <td><strong>${stat.label}</strong></td>
                    <td>${stat.value}</td>
                </tr>
            `;
        });

        statsTable.innerHTML = html;
    }

    async searchKnowledgeGraph() {
        const searchInput = document.getElementById('kg-search-input');
        const query = searchInput.value.trim();
        
        if (!query) return;

        const resultsContainer = document.getElementById('kg-search-results');
        resultsContainer.innerHTML = '<div class="text-center"><div class="spinner-border" role="status"></div></div>';

        try {
            const response = await fetch('/api/search', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ query: query, limit: 10 })
            });

            const data = await response.json();
            
            if (data.status === 'success') {
                this.displaySearchResults(data.results);
            } else {
                throw new Error(data.message || 'Search failed');
            }
        } catch (error) {
            console.error('Search error:', error);
            resultsContainer.innerHTML = `<div class="alert alert-danger">Error: ${error.message}</div>`;
        }
    }

    displaySearchResults(results) {
        const resultsContainer = document.getElementById('kg-search-results');
        
        if (results.length === 0) {
            resultsContainer.innerHTML = '<div class="text-muted text-center">No results found</div>';
            return;
        }

        let html = '';
        results.forEach(result => {
            html += `
                <div class="search-result-item">
                    <div class="result-title">${result.name}</div>
                    <div class="d-flex justify-content-between align-items-center">
                        <span class="result-type">${result.type}</span>
                        <span class="result-similarity">${(result.similarity * 100).toFixed(1)}%</span>
                    </div>
                    <div class="result-description mt-2">
                        <small class="text-muted">${result.description}</small>
                    </div>
                </div>
            `;
        });

        resultsContainer.innerHTML = html;
    }

    async scrapePortal() {
        const urlInput = document.getElementById('portal-url');
        const url = urlInput.value.trim();
        
        if (!url) {
            this.showError('Please enter a valid URL');
            return;
        }

        const progressContainer = document.getElementById('scraping-progress');
        const resultsContainer = document.getElementById('scraping-results');
        
        // Show progress
        progressContainer.style.display = 'block';
        resultsContainer.innerHTML = '';

        try {
            const response = await fetch('/api/scrape_portal', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ url: url })
            });

            const data = await response.json();
            
            if (data.status === 'success') {
                resultsContainer.innerHTML = `
                    <div class="scraping-result">
                        <strong>Success!</strong> ${data.message}
                    </div>
                `;
            } else {
                throw new Error(data.message || 'Scraping failed');
            }
        } catch (error) {
            console.error('Scraping error:', error);
            resultsContainer.innerHTML = `
                <div class="scraping-result scraping-error">
                    <strong>Error:</strong> ${error.message}
                </div>
            `;
        } finally {
            progressContainer.style.display = 'none';
        }
    }

    loadSystemLogs() {
        const logsContainer = document.getElementById('system-logs');
        
        // Mock log entries
        const logEntries = [
            { timestamp: new Date().toISOString(), level: 'INFO', message: 'System started successfully' },
            { timestamp: new Date(Date.now() - 60000).toISOString(), level: 'INFO', message: 'Knowledge graph loaded with 45 entities' },
            { timestamp: new Date(Date.now() - 120000).toISOString(), level: 'WARNING', message: 'Low confidence query processed' },
            { timestamp: new Date(Date.now() - 180000).toISOString(), level: 'INFO', message: 'Portal content scraped successfully' },
            { timestamp: new Date(Date.now() - 240000).toISOString(), level: 'ERROR', message: 'Failed to connect to external API' },
            { timestamp: new Date(Date.now() - 300000).toISOString(), level: 'DEBUG', message: 'NLP processor initialized' }
        ];

        let html = '';
        logEntries.forEach(entry => {
            const time = new Date(entry.timestamp).toLocaleTimeString();
            html += `
                <div class="log-entry">
                    <span class="log-timestamp">[${time}]</span>
                    <span class="log-level-${entry.level.toLowerCase()}">${entry.level}</span>
                    <span class="log-message">${entry.message}</span>
                </div>
            `;
        });

        logsContainer.innerHTML = html;
    }

    refreshLogs() {
        this.loadSystemLogs();
        this.showSuccess('Logs refreshed');
    }

    showLoading() {
        if (this.loadingOverlay) return;
        
        this.loadingOverlay = document.createElement('div');
        this.loadingOverlay.className = 'loading-overlay';
        this.loadingOverlay.innerHTML = '<div class="loading-spinner"></div>';
        document.body.appendChild(this.loadingOverlay);
    }

    hideLoading() {
        if (this.loadingOverlay) {
            this.loadingOverlay.remove();
            this.loadingOverlay = null;
        }
    }

    showError(message) {
        this.showToast(message, 'danger');
    }

    showSuccess(message) {
        this.showToast(message, 'success');
    }

    showToast(message, type = 'info') {
        const toast = document.createElement('div');
        toast.className = `toast align-items-center text-white bg-${type} border-0`;
        toast.setAttribute('role', 'alert');
        
        toast.innerHTML = `
            <div class="d-flex">
                <div class="toast-body">${message}</div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" 
                        data-bs-dismiss="toast"></button>
            </div>
        `;

        let toastContainer = document.querySelector('.toast-container');
        if (!toastContainer) {
            toastContainer = document.createElement('div');
            toastContainer.className = 'toast-container position-fixed top-0 end-0 p-3';
            document.body.appendChild(toastContainer);
        }

        toastContainer.appendChild(toast);
        const bsToast = new bootstrap.Toast(toast);
        bsToast.show();

        toast.addEventListener('hidden.bs.toast', () => {
            toast.remove();
        });
    }
}

// Global functions for HTML onclick handlers
function showSection(sectionName) {
    if (window.adminInterface) {
        window.adminInterface.showSection(sectionName);
    }
}

function searchKnowledgeGraph() {
    if (window.adminInterface) {
        window.adminInterface.searchKnowledgeGraph();
    }
}

function scrapePortal() {
    if (window.adminInterface) {
        window.adminInterface.scrapePortal();
    }
}

function refreshLogs() {
    if (window.adminInterface) {
        window.adminInterface.refreshLogs();
    }
}

// Initialize admin interface when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.adminInterface = new AdminInterface();
    console.log('Admin interface loaded');
});