/**
 * API Client for Retire-Cluster Dashboard
 */

class RetireClusterAPI {
    constructor(config) {
        this.config = config;
        this.baseUrl = config.apiBaseUrl;
        this.apiVersion = config.apiVersion;
        this.apiKey = config.utils.getSetting('apiKey');
        this.retryCount = 0;
        this.maxRetries = config.maxRetries;
        this.retryDelay = config.retryDelay;
    }

    /**
     * Get API endpoint URL
     */
    getUrl(endpoint) {
        return `${this.baseUrl}/api/${this.apiVersion}${endpoint}`;
    }

    /**
     * Get request headers
     */
    getHeaders(contentType = 'application/json') {
        const headers = {
            'Content-Type': contentType,
            'Accept': 'application/json'
        };

        if (this.apiKey) {
            headers['Authorization'] = `Bearer ${this.apiKey}`;
        }

        return headers;
    }

    /**
     * Make HTTP request with retry logic
     */
    async request(method, endpoint, data = null, options = {}) {
        const url = this.getUrl(endpoint);
        const config = {
            method: method.toUpperCase(),
            headers: this.getHeaders(options.contentType),
            ...options
        };

        if (data && (method.toUpperCase() === 'POST' || method.toUpperCase() === 'PUT')) {
            config.body = typeof data === 'string' ? data : JSON.stringify(data);
        }

        try {
            const response = await fetch(url, config);
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            // Reset retry count on success
            this.retryCount = 0;

            const contentType = response.headers.get('content-type');
            if (contentType && contentType.includes('application/json')) {
                return await response.json();
            } else {
                return await response.text();
            }
        } catch (error) {
            console.error(`API Request failed: ${method} ${endpoint}`, error);
            
            // Retry logic
            if (this.retryCount < this.maxRetries) {
                this.retryCount++;
                console.log(`Retrying request (${this.retryCount}/${this.maxRetries}) in ${this.retryDelay}ms`);
                
                await new Promise(resolve => setTimeout(resolve, this.retryDelay));
                return this.request(method, endpoint, data, options);
            }
            
            throw error;
        }
    }

    // Convenience methods
    async get(endpoint, options = {}) {
        return this.request('GET', endpoint, null, options);
    }

    async post(endpoint, data, options = {}) {
        return this.request('POST', endpoint, data, options);
    }

    async put(endpoint, data, options = {}) {
        return this.request('PUT', endpoint, data, options);
    }

    async delete(endpoint, options = {}) {
        return this.request('DELETE', endpoint, null, options);
    }

    // Cluster API methods
    async getClusterStatus() {
        return this.get('/cluster/status');
    }

    async getClusterHealth() {
        return this.get('/cluster/health');
    }

    async getClusterMetrics() {
        return this.get('/cluster/metrics');
    }

    // Device API methods
    async getDevices(filters = {}) {
        const params = new URLSearchParams();
        Object.keys(filters).forEach(key => {
            if (filters[key]) params.append(key, filters[key]);
        });
        
        const query = params.toString();
        return this.get(`/devices${query ? '?' + query : ''}`);
    }

    async getDevice(deviceId) {
        return this.get(`/devices/${encodeURIComponent(deviceId)}`);
    }

    async updateDevice(deviceId, data) {
        return this.put(`/devices/${encodeURIComponent(deviceId)}`, data);
    }

    async removeDevice(deviceId) {
        return this.delete(`/devices/${encodeURIComponent(deviceId)}`);
    }

    async getDeviceMetrics(deviceId, timeRange = '1h') {
        return this.get(`/devices/${encodeURIComponent(deviceId)}/metrics?range=${timeRange}`);
    }

    async getDeviceLogs(deviceId, limit = 100) {
        return this.get(`/devices/${encodeURIComponent(deviceId)}/logs?limit=${limit}`);
    }

    // Task API methods
    async getTasks(filters = {}) {
        const params = new URLSearchParams();
        Object.keys(filters).forEach(key => {
            if (filters[key]) params.append(key, filters[key]);
        });
        
        const query = params.toString();
        return this.get(`/tasks${query ? '?' + query : ''}`);
    }

    async getTask(taskId) {
        return this.get(`/tasks/${encodeURIComponent(taskId)}`);
    }

    async submitTask(taskData) {
        return this.post('/tasks', taskData);
    }

    async cancelTask(taskId) {
        return this.post(`/tasks/${encodeURIComponent(taskId)}/cancel`);
    }

    async getTaskResult(taskId) {
        return this.get(`/tasks/${encodeURIComponent(taskId)}/result`);
    }

    async getTaskLogs(taskId) {
        return this.get(`/tasks/${encodeURIComponent(taskId)}/logs`);
    }

    // Log API methods
    async getLogs(filters = {}) {
        const params = new URLSearchParams();
        Object.keys(filters).forEach(key => {
            if (filters[key]) params.append(key, filters[key]);
        });
        
        const query = params.toString();
        return this.get(`/logs${query ? '?' + query : ''}`);
    }

    // Configuration API methods
    async getConfig() {
        return this.get('/config');
    }

    async updateConfig(configData) {
        return this.put('/config', configData);
    }

    // System API methods
    async getSystemInfo() {
        return this.get('/system/info');
    }

    async getSystemHealth() {
        return this.get('/system/health');
    }

    // Authentication methods
    async authenticate(credentials) {
        return this.post('/auth/login', credentials);
    }

    async refreshToken() {
        return this.post('/auth/refresh');
    }

    async logout() {
        return this.post('/auth/logout');
    }

    // Export methods
    async exportData(type, format = 'json', filters = {}) {
        const params = new URLSearchParams({
            format,
            ...filters
        });
        
        return this.get(`/export/${type}?${params.toString()}`, {
            contentType: 'application/octet-stream'
        });
    }

    async exportDevices(format = 'json', filters = {}) {
        return this.exportData('devices', format, filters);
    }

    async exportTasks(format = 'json', filters = {}) {
        return this.exportData('tasks', format, filters);
    }

    async exportLogs(format = 'json', filters = {}) {
        return this.exportData('logs', format, filters);
    }

    // Real-time streaming methods
    createEventSource(endpoint, onMessage, onError) {
        const url = `${this.baseUrl}/stream${endpoint}`;
        const eventSource = new EventSource(url);
        
        eventSource.onmessage = onMessage;
        eventSource.onerror = onError || ((error) => {
            console.error('EventSource error:', error);
        });
        
        return eventSource;
    }

    streamDevices(onUpdate, onError) {
        return this.createEventSource('/devices', (event) => {
            try {
                const data = JSON.parse(event.data);
                onUpdate(data);
            } catch (error) {
                console.error('Error parsing device stream data:', error);
            }
        }, onError);
    }

    streamLogs(onUpdate, onError, filters = {}) {
        const params = new URLSearchParams(filters);
        const query = params.toString();
        
        return this.createEventSource(`/logs${query ? '?' + query : ''}`, (event) => {
            try {
                const data = JSON.parse(event.data);
                onUpdate(data);
            } catch (error) {
                console.error('Error parsing log stream data:', error);
            }
        }, onError);
    }

    streamTasks(onUpdate, onError) {
        return this.createEventSource('/tasks', (event) => {
            try {
                const data = JSON.parse(event.data);
                onUpdate(data);
            } catch (error) {
                console.error('Error parsing task stream data:', error);
            }
        }, onError);
    }

    // Utility methods
    setApiKey(apiKey) {
        this.apiKey = apiKey;
        this.config.utils.setSetting('apiKey', apiKey);
    }

    clearApiKey() {
        this.apiKey = null;
        localStorage.removeItem(this.config.storageKeys.apiKey);
    }

    isAuthenticated() {
        return !!this.apiKey;
    }

    // Health check
    async healthCheck() {
        try {
            await this.get('/health');
            return true;
        } catch (error) {
            return false;
        }
    }
}

// Create global API instance
window.api = new RetireClusterAPI(window.RetireClusterConfig);

// Export for modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = RetireClusterAPI;
}

console.log('Retire-Cluster API Client loaded successfully');