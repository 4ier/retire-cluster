/**
 * Device management functionality for Retire-Cluster
 */

class DeviceManager {
    constructor(api, config) {
        this.api = api;
        this.config = config;
        this.devices = [];
        this.filteredDevices = [];
        this.currentFilters = { status: 'all', search: '' };
        
        this.init = this.init.bind(this);
        this.loadDevices = this.loadDevices.bind(this);
        this.filterDevices = this.filterDevices.bind(this);
        this.renderDevices = this.renderDevices.bind(this);
    }

    async init() {
        console.log('Initializing device manager...');
        
        try {
            await this.loadDevices();
            this.setupEventListeners();
            console.log('Device manager initialized successfully');
        } catch (error) {
            console.error('Failed to initialize device manager:', error);
        }
    }

    async loadDevices() {
        try {
            const response = await this.api.getDevices();
            this.devices = response.data?.devices || response;
            this.filterDevices();
            this.renderDevices();
        } catch (error) {
            console.error('Failed to load devices:', error);
            this.showError('Failed to load devices');
        }
    }

    filterDevices() {
        this.filteredDevices = this.devices.filter(device => {
            // Status filter
            if (this.currentFilters.status !== 'all' && device.status !== this.currentFilters.status) {
                return false;
            }
            
            // Search filter
            if (this.currentFilters.search) {
                const searchLower = this.currentFilters.search.toLowerCase();
                return device.id?.toLowerCase().includes(searchLower) ||
                       device.platform?.toLowerCase().includes(searchLower) ||
                       device.hostname?.toLowerCase().includes(searchLower);
            }
            
            return true;
        });
    }

    renderDevices() {
        const container = document.getElementById('devicesGrid');
        if (!container) return;

        container.innerHTML = '';

        if (this.filteredDevices.length === 0) {
            container.innerHTML = `
                <div class="no-devices">
                    <i class="fas fa-server" style="font-size: 3rem; color: var(--text-muted); margin-bottom: 1rem;"></i>
                    <h3>No devices found</h3>
                    <p>Try adjusting your filters or add a new device.</p>
                </div>
            `;
            return;
        }

        this.filteredDevices.forEach(device => {
            const deviceCard = this.createDeviceCard(device);
            container.appendChild(deviceCard);
        });
    }

    createDeviceCard(device) {
        const card = document.createElement('div');
        card.className = 'device-card fade-in';
        card.onclick = () => this.showDeviceDetails(device);

        const statusClass = device.status || 'offline';
        const lastSeen = device.last_heartbeat ? 
            this.formatLastSeen(new Date(device.last_heartbeat)) : 'Never';
        
        const cpuUsage = device.cpu_usage || 0;
        const memoryUsage = device.memory_usage || 0;
        const diskUsage = device.disk_usage || 0;

        card.innerHTML = `
            <div class="device-header">
                <div class="device-name">
                    <i class="fas fa-${this.getDeviceIcon(device.platform)}"></i>
                    ${device.id || 'Unknown'}
                </div>
                <div class="device-status ${statusClass}">
                    ${statusClass}
                </div>
            </div>
            
            <div class="device-info">
                <div class="device-info-row">
                    <span class="label">Platform:</span>
                    <span class="value">${device.platform || 'Unknown'}</span>
                </div>
                <div class="device-info-row">
                    <span class="label">IP:</span>
                    <span class="value">${device.ip || 'N/A'}</span>
                </div>
                <div class="device-info-row">
                    <span class="label">Last Seen:</span>
                    <span class="value">${lastSeen}</span>
                </div>
            </div>
            
            <div class="device-metrics">
                <div class="device-metric">
                    <div class="device-metric-value">${cpuUsage}%</div>
                    <div class="device-metric-label">CPU</div>
                    <div class="progress-bar">
                        <div class="progress-fill" style="width: ${cpuUsage}%;"></div>
                    </div>
                </div>
                <div class="device-metric">
                    <div class="device-metric-value">${memoryUsage}%</div>
                    <div class="device-metric-label">Memory</div>
                    <div class="progress-bar">
                        <div class="progress-fill" style="width: ${memoryUsage}%;"></div>
                    </div>
                </div>
            </div>
            
            <div class="device-actions">
                <button class="btn btn-sm btn-secondary" onclick="event.stopPropagation(); window.deviceManager.viewLogs('${device.id}')">
                    <i class="fas fa-file-alt"></i> Logs
                </button>
                <button class="btn btn-sm btn-secondary" onclick="event.stopPropagation(); window.deviceManager.assignTask('${device.id}')">
                    <i class="fas fa-play"></i> Run Task
                </button>
            </div>
        `;

        return card;
    }

    getDeviceIcon(platform) {
        const iconMap = {
            'windows': 'laptop',
            'linux': 'server',
            'darwin': 'laptop-mac',
            'macos': 'laptop-mac',
            'android': 'mobile-alt',
            'ios': 'mobile-alt'
        };
        return iconMap[platform?.toLowerCase()] || 'server';
    }

    formatLastSeen(date) {
        const now = new Date();
        const diff = now - date;
        const minutes = Math.floor(diff / 60000);
        const hours = Math.floor(minutes / 60);
        const days = Math.floor(hours / 24);

        if (minutes < 1) return 'Just now';
        if (minutes < 60) return `${minutes}m ago`;
        if (hours < 24) return `${hours}h ago`;
        return `${days}d ago`;
    }

    setupEventListeners() {
        // Search input
        const searchInput = document.getElementById('deviceSearch');
        if (searchInput) {
            searchInput.addEventListener('input', this.config.utils.debounce((e) => {
                this.currentFilters.search = e.target.value;
                this.filterDevices();
                this.renderDevices();
            }, 300));
        }

        // Status filter
        const statusFilter = document.getElementById('deviceFilter');
        if (statusFilter) {
            statusFilter.addEventListener('change', (e) => {
                this.currentFilters.status = e.target.value;
                this.filterDevices();
                this.renderDevices();
            });
        }
    }

    async showDeviceDetails(device) {
        try {
            // Get detailed device info
            const deviceDetails = await this.api.getDevice(device.id);
            const deviceData = deviceDetails.data || deviceDetails;
            
            // Show modal with device details
            this.showDeviceModal(deviceData);
            
        } catch (error) {
            console.error('Failed to get device details:', error);
            this.showError('Failed to load device details');
        }
    }

    showDeviceModal(device) {
        const modal = document.getElementById('deviceModal');
        const details = document.getElementById('deviceDetails');
        
        if (!modal || !details) return;

        const lastSeen = device.last_heartbeat ? 
            new Date(device.last_heartbeat).toLocaleString() : 'Never';
        
        details.innerHTML = `
            <div class="device-details-grid">
                <div class="detail-section">
                    <h4>Basic Information</h4>
                    <div class="detail-item">
                        <span class="label">Device ID:</span>
                        <span class="value">${device.id}</span>
                    </div>
                    <div class="detail-item">
                        <span class="label">Platform:</span>
                        <span class="value">${device.platform || 'Unknown'}</span>
                    </div>
                    <div class="detail-item">
                        <span class="label">Hostname:</span>
                        <span class="value">${device.hostname || 'N/A'}</span>
                    </div>
                    <div class="detail-item">
                        <span class="label">IP Address:</span>
                        <span class="value">${device.ip || 'N/A'}</span>
                    </div>
                    <div class="detail-item">
                        <span class="label">Status:</span>
                        <span class="value status-${device.status}">${device.status}</span>
                    </div>
                    <div class="detail-item">
                        <span class="label">Last Seen:</span>
                        <span class="value">${lastSeen}</span>
                    </div>
                </div>
                
                <div class="detail-section">
                    <h4>System Specifications</h4>
                    <div class="detail-item">
                        <span class="label">CPU Cores:</span>
                        <span class="value">${device.cpu_cores || 'N/A'}</span>
                    </div>
                    <div class="detail-item">
                        <span class="label">Memory:</span>
                        <span class="value">${this.config.utils.formatBytes((device.memory_total || 0) * 1024 * 1024 * 1024)}</span>
                    </div>
                    <div class="detail-item">
                        <span class="label">Disk Space:</span>
                        <span class="value">${this.config.utils.formatBytes((device.disk_total || 0) * 1024 * 1024 * 1024)}</span>
                    </div>
                    <div class="detail-item">
                        <span class="label">Architecture:</span>
                        <span class="value">${device.architecture || 'N/A'}</span>
                    </div>
                </div>
                
                <div class="detail-section">
                    <h4>Current Usage</h4>
                    <div class="usage-meters">
                        <div class="usage-meter">
                            <div class="usage-label">CPU Usage</div>
                            <div class="usage-bar">
                                <div class="usage-fill" style="width: ${device.cpu_usage || 0}%"></div>
                            </div>
                            <div class="usage-value">${device.cpu_usage || 0}%</div>
                        </div>
                        <div class="usage-meter">
                            <div class="usage-label">Memory Usage</div>
                            <div class="usage-bar">
                                <div class="usage-fill" style="width: ${device.memory_usage || 0}%"></div>
                            </div>
                            <div class="usage-value">${device.memory_usage || 0}%</div>
                        </div>
                        <div class="usage-meter">
                            <div class="usage-label">Disk Usage</div>
                            <div class="usage-bar">
                                <div class="usage-fill" style="width: ${device.disk_usage || 0}%"></div>
                            </div>
                            <div class="usage-value">${device.disk_usage || 0}%</div>
                        </div>
                    </div>
                </div>
                
                <div class="detail-section">
                    <h4>Task History</h4>
                    <div class="task-stats">
                        <div class="stat-item">
                            <span class="stat-value">${device.tasks_completed || 0}</span>
                            <span class="stat-label">Completed</span>
                        </div>
                        <div class="stat-item">
                            <span class="stat-value">${device.tasks_failed || 0}</span>
                            <span class="stat-label">Failed</span>
                        </div>
                        <div class="stat-item">
                            <span class="stat-value">${device.tasks_running || 0}</span>
                            <span class="stat-label">Running</span>
                        </div>
                    </div>
                </div>
            </div>
        `;

        modal.classList.add('active');
    }

    async viewLogs(deviceId) {
        try {
            const logs = await this.api.getDeviceLogs(deviceId, 50);
            console.log(`Device ${deviceId} logs:`, logs);
            // Could show logs in a modal or navigate to logs page
            this.showNotification(`Viewing logs for ${deviceId}`, 'info');
        } catch (error) {
            console.error('Failed to get device logs:', error);
            this.showError('Failed to load device logs');
        }
    }

    async assignTask(deviceId) {
        // Show task assignment modal
        console.log(`Assigning task to device ${deviceId}`);
        this.showNotification(`Task assignment for ${deviceId} - feature coming soon`, 'info');
    }

    async removeDevice(deviceId) {
        if (!confirm(`Are you sure you want to remove device ${deviceId}?`)) {
            return;
        }

        try {
            await this.api.removeDevice(deviceId);
            this.showNotification(`Device ${deviceId} removed successfully`, 'success');
            await this.loadDevices();
            this.closeModal('deviceModal');
        } catch (error) {
            console.error('Failed to remove device:', error);
            this.showError('Failed to remove device');
        }
    }

    closeModal(modalId) {
        const modal = document.getElementById(modalId);
        if (modal) {
            modal.classList.remove('active');
        }
    }

    showNotification(message, type = 'info') {
        if (window.dashboard) {
            window.dashboard.showNotification(message, type);
        } else {
            console.log(`${type.toUpperCase()}: ${message}`);
        }
    }

    showError(message) {
        this.showNotification(message, 'error');
    }

    showSuccess(message) {
        this.showNotification(message, 'success');
    }

    // Auto-refresh devices
    startAutoRefresh() {
        if (this.refreshTimer) {
            clearInterval(this.refreshTimer);
        }
        
        this.refreshTimer = setInterval(() => {
            this.loadDevices();
        }, this.config.deviceRefreshInterval);
    }

    stopAutoRefresh() {
        if (this.refreshTimer) {
            clearInterval(this.refreshTimer);
            this.refreshTimer = null;
        }
    }
}

// Create global device manager instance
window.deviceManager = new DeviceManager(window.api, window.RetireClusterConfig);

// Export functions that may be called from HTML
window.showAddDeviceModal = () => {
    console.log('Add device modal - feature coming soon');
    window.deviceManager.showNotification('Add device feature coming soon', 'info');
};

window.removeDevice = () => {
    const modal = document.getElementById('deviceModal');
    const deviceId = modal?.querySelector('[data-device-id]')?.dataset.deviceId;
    if (deviceId) {
        window.deviceManager.removeDevice(deviceId);
    }
};

window.closeModal = (modalId) => {
    window.deviceManager.closeModal(modalId);
};

console.log('Device Manager loaded successfully');