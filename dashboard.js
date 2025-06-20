class HoneypotDashboard {
    constructor() {
        this.charts = {};
        this.map = null;
        this.updateInterval = 30000; // 30 seconds
        this.autoUpdateEnabled = true;
        this.init();
    }

    init() {
        this.initializeCharts();
        this.initializeMap();
        this.startAutoUpdate();
        this.bindEvents();
        this.loadInitialData();
    }

    initializeCharts() {
        // Initialize Attack Timeline Chart
        const timelineCtx = document.getElementById('attackTimelineChart');
        if (timelineCtx) {
            this.charts.timeline = new Chart(timelineCtx, {
                type: 'line',
                data: {
                    labels: [],
                    datasets: [{
                        label: 'Attacks per Hour',
                        data: [],
                        borderColor: 'rgb(75, 192, 192)',
                        backgroundColor: 'rgba(75, 192, 192, 0.2)',
                        tension: 0.4
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        title: {
                            display: true,
                            text: 'Attack Timeline (Last 24 Hours)'
                        }
                    },
                    scales: {
                        y: {
                            beginAtZero: true
                        }
                    }
                }
            });
        }

        // Initialize Country Distribution Chart
        const countryCtx = document.getElementById('countryChart');
        if (countryCtx) {
            this.charts.country = new Chart(countryCtx, {
                type: 'doughnut',
                data: {
                    labels: [],
                    datasets: [{
                        data: [],
                        backgroundColor: [
                            '#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0',
                            '#9966FF', '#FF9F40', '#FF6384', '#C9CBCF',
                            '#4BC0C0', '#FF6384'
                        ]
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        title: {
                            display: true,
                            text: 'Attacks by Country'
                        },
                        legend: {
                            position: 'right'
                        }
                    }
                }
            });
        }

        // Initialize Credentials Chart
        const credentialsCtx = document.getElementById('credentialsChart');
        if (credentialsCtx) {
            this.charts.credentials = new Chart(credentialsCtx, {
                type: 'bar',
                data: {
                    labels: [],
                    datasets: [{
                        label: 'Username Attempts',
                        data: [],
                        backgroundColor: 'rgba(54, 162, 235, 0.8)'
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        title: {
                            display: true,
                            text: 'Most Common Usernames'
                        }
                    },
                    scales: {
                        y: {
                            beginAtZero: true
                        }
                    }
                }
            });
        }
    }

    initializeMap() {
        const mapContainer = document.getElementById('attackMap');
        if (mapContainer) {
            this.map = L.map('attackMap').setView([20, 0], 2);
            
            L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
                attribution: '© OpenStreetMap contributors'
            }).addTo(this.map);

            this.attackMarkers = L.layerGroup().addTo(this.map);
        }
    }

    bindEvents() {
        // Auto-update toggle
        const autoUpdateToggle = document.getElementById('autoUpdateToggle');
        if (autoUpdateToggle) {
            autoUpdateToggle.addEventListener('change', (e) => {
                this.autoUpdateEnabled = e.target.checked;
                if (this.autoUpdateEnabled) {
                    this.startAutoUpdate();
                } else {
                    this.stopAutoUpdate();
                }
            });
        }

        // Manual refresh button
        const refreshBtn = document.getElementById('refreshBtn');
        if (refreshBtn) {
            refreshBtn.addEventListener('click', () => {
                this.loadInitialData();
            });
        }

        // Time range selector
        const timeRangeSelect = document.getElementById('timeRange');
        if (timeRangeSelect) {
            timeRangeSelect.addEventListener('change', () => {
                this.loadInitialData();
            });
        }
    }

    startAutoUpdate() {
        if (this.updateTimer) {
            clearInterval(this.updateTimer);
        }
        
        if (this.autoUpdateEnabled) {
            this.updateTimer = setInterval(() => {
                this.loadInitialData();
            }, this.updateInterval);
        }
    }

    stopAutoUpdate() {
        if (this.updateTimer) {
            clearInterval(this.updateTimer);
            this.updateTimer = null;
        }
    }

    async loadInitialData() {
        this.showLoading();
        
        try {
            await Promise.all([
                this.updateTimelineChart(),
                this.updateCountryChart(),
                this.updateCredentialsChart(),
                this.updateMap(),
                this.updateRecentAttacks()
            ]);
        } catch (error) {
            console.error('Error loading dashboard data:', error);
            this.showError('Failed to load dashboard data');
        } finally {
            this.hideLoading();
        }
    }

    async updateTimelineChart() {
        try {
            const timeRange = document.getElementById('timeRange')?.value || '24';
            const response = await fetch(`/api/attacks/by-hour?hours=${timeRange}`);
            const data = await response.json();

            if (this.charts.timeline) {
                const labels = data.map(item => {
                    const date = new Date(item.hour);
                    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
                });
                const counts = data.map(item => item.count);

                this.charts.timeline.data.labels = labels;
                this.charts.timeline.data.datasets[0].data = counts;
                this.charts.timeline.update();
            }
        } catch (error) {
            console.error('Error updating timeline chart:', error);
        }
    }

    async updateCountryChart() {
        try {
            const response = await fetch('/api/attacks/by-country');
            const data = await response.json();

            if (this.charts.country) {
                const labels = data.map(item => item.country);
                const counts = data.map(item => item.count);

                this.charts.country.data.labels = labels;
                this.charts.country.data.datasets[0].data = counts;
                this.charts.country.update();
            }
        } catch (error) {
            console.error('Error updating country chart:', error);
        }
    }

    async updateCredentialsChart() {
        try {
            const response = await fetch('/api/top-credentials');
            const data = await response.json();

            if (this.charts.credentials && data.usernames) {
                const labels = data.usernames.map(item => item.username);
                const counts = data.usernames.map(item => item.count);

                this.charts.credentials.data.labels = labels;
                this.charts.credentials.data.datasets[0].data = counts;
                this.charts.credentials.update();
            }
        } catch (error) {
            console.error('Error updating credentials chart:', error);
        }
    }

    async updateMap() {
        try {
            const response = await fetch('/api/attacks/map-data');
            const data = await response.json();

            if (this.map && this.attackMarkers) {
                this.attackMarkers.clearLayers();

                data.forEach(location => {
                    if (location.latitude && location.longitude) {
                        const marker = L.circleMarker([location.latitude, location.longitude], {
                            radius: Math.min(8 + Math.log(location.count), 20),
                            fillColor: '#ff0000',
                            color: '#ff0000',
                            weight: 1,
                            opacity: 0.8,
                            fillOpacity: 0.6
                        });

                        const popupContent = `
                            <div>
                                <h6>${location.city}, ${location.country}</h6>
                                <p><strong>Attacks:</strong> ${location.count}</p>
                                <div class="recent-attacks">
                                    <strong>Recent attacks:</strong>
                                    <ul class="list-unstyled mt-1">
                                        ${location.recent_attacks.slice(0, 3).map(attack => 
                                            `<li class="small">
                                                ${attack.source_ip} (${attack.username || 'unknown'})
                                                <br><small class="text-muted">${new Date(attack.timestamp).toLocaleString()}</small>
                                            </li>`
                                        ).join('')}
                                    </ul>
                                </div>
                            </div>
                        `;

                        marker.bindPopup(popupContent);
                        this.attackMarkers.addLayer(marker);
                    }
                });
            }
        } catch (error) {
            console.error('Error updating map:', error);
        }
    }

    async updateRecentAttacks() {
        try {
            const response = await fetch('/api/attacks/recent?hours=1');
            const data = await response.json();

            const container = document.getElementById('recentAttacks');
            if (container) {
                container.innerHTML = '';

                if (data.length === 0) {
                    container.innerHTML = '<div class="text-muted">No recent attacks in the last hour</div>';
                    return;
                }

                data.slice(0, 10).forEach(attack => {
                    const attackElement = document.createElement('div');
                    attackElement.className = 'attack-item';
                    attackElement.innerHTML = `
                        <div class="d-flex justify-content-between align-items-start">
                            <div>
                                <div class="fw-bold ip-address">${attack.source_ip}:${attack.source_port}</div>
                                <div class="small">
                                    <span class="credential">${attack.username || 'unknown'}</span> / 
                                    <span class="credential">${attack.password || 'unknown'}</span>
                                </div>
                                <div class="small text-muted">
                                    ${attack.city || 'Unknown'}, ${attack.country || 'Unknown'}
                                </div>
                            </div>
                            <div class="small timestamp">
                                ${new Date(attack.timestamp).toLocaleString()}
                            </div>
                        </div>
                    `;
                    container.appendChild(attackElement);
                });
            }
        } catch (error) {
            console.error('Error updating recent attacks:', error);
        }
    }

    showLoading() {
        const spinner = document.querySelector('.loading-spinner');
        if (spinner) {
            spinner.classList.add('show');
        }
    }

    hideLoading() {
        const spinner = document.querySelector('.loading-spinner');
        if (spinner) {
            spinner.classList.remove('show');
        }
    }

    showError(message) {
        const errorContainer = document.getElementById('errorContainer');
        if (errorContainer) {
            errorContainer.innerHTML = `
                <div class="alert alert-danger alert-dismissible fade show" role="alert">
                    ${message}
                    <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
                </div>
            `;
        }
    }
}

// Initialize dashboard when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    window.dashboard = new HoneypotDashboard();
});

// Utility functions for other pages
window.HoneypotUtils = {
    formatTimestamp: function(timestamp) {
        return new Date(timestamp).toLocaleString();
    },

    formatIP: function(ip) {
        return `<span class="ip-address">${ip}</span>`;
    },

    formatCredential: function(credential) {
        return `<span class="credential">${credential || 'unknown'}</span>`;
    }
};
