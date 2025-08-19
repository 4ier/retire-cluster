/**
 * Configuration for Retire-Cluster Dashboard
 */

window.RetireClusterConfig = {
    // API Configuration
    apiBaseUrl: window.location.origin,
    apiVersion: 'v1',
    
    // Refresh intervals (in milliseconds)
    refreshInterval: 5000,      // General dashboard refresh
    deviceRefreshInterval: 3000, // Device status refresh
    taskRefreshInterval: 2000,   // Task status refresh
    logRefreshInterval: 1000,    // Log refresh
    
    // UI Configuration
    theme: localStorage.getItem('theme') || 'dark',
    enableNotifications: localStorage.getItem('enableNotifications') !== 'false',
    enableSound: localStorage.getItem('enableSound') === 'true',
    autoRefresh: localStorage.getItem('autoRefresh') !== 'false',
    
    // Chart Configuration
    chartColors: {
        primary: '#667eea',
        secondary: '#764ba2',
        accent: '#f093fb',
        success: '#43e97b',
        warning: '#feca57',
        error: '#ff6b6b',
        info: '#4facfe'
    },
    
    // Table Configuration
    defaultPageSize: 10,
    maxPageSize: 100,
    
    // Device Configuration
    deviceStatusColors: {
        online: '#43e97b',
        offline: '#ff6b6b',
        warning: '#feca57',
        maintenance: '#4facfe'
    },
    
    // Task Configuration
    taskStatusColors: {
        running: '#4facfe',
        queued: '#feca57',
        completed: '#43e97b',
        failed: '#ff6b6b',
        cancelled: '#a0a0a0'
    },
    
    // Priority Configuration
    taskPriorities: {
        low: { color: '#a0a0a0', weight: 1 },
        normal: { color: '#4facfe', weight: 2 },
        high: { color: '#feca57', weight: 3 },
        urgent: { color: '#ff6b6b', weight: 4 }
    },
    
    // Export Configuration
    exportFormats: ['json', 'csv', 'tsv', 'xml'],
    
    // Animation Configuration
    animationDuration: 300,
    chartAnimationDuration: 1000,
    
    // Error Configuration
    maxRetries: 3,
    retryDelay: 1000,
    
    // Storage keys
    storageKeys: {
        theme: 'theme',
        apiKey: 'apiKey',
        refreshInterval: 'refreshInterval',
        enableNotifications: 'enableNotifications',
        enableSound: 'enableSound',
        autoRefresh: 'autoRefresh',
        selectedDeviceFilters: 'selectedDeviceFilters',
        selectedTaskFilters: 'selectedTaskFilters',
        dashboardLayout: 'dashboardLayout'
    },
    
    // Validation patterns
    patterns: {
        deviceId: /^[a-z0-9][a-z0-9-]*[a-z0-9]$/,
        ipAddress: /^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$/,
        port: /^([1-9][0-9]{0,3}|[1-5][0-9]{4}|6[0-4][0-9]{3}|65[0-4][0-9]{2}|655[0-2][0-9]|6553[0-5])$/,
        email: /^[^\s@]+@[^\s@]+\.[^\s@]+$/
    },
    
    // Feature flags
    features: {
        realTimeMonitoring: true,
        deviceGrouping: true,
        taskScheduling: true,
        exportData: true,
        systemMetrics: true,
        logStreaming: true,
        notifications: true,
        multiTenant: false,
        advancedFiltering: true,
        customDashboard: false
    },
    
    // Default values
    defaults: {
        taskType: 'echo',
        taskPriority: 'normal',
        deviceFilter: 'all',
        taskFilter: 'all',
        chartTimeRange: '24h',
        logLevel: 'INFO'
    }
};

// Utility functions
window.RetireClusterConfig.utils = {
    /**
     * Get API endpoint URL
     */
    getApiUrl: function(endpoint) {
        return `${this.apiBaseUrl}/api/${this.apiVersion}${endpoint}`;
    },
    
    /**
     * Get stored configuration value
     */
    getSetting: function(key, defaultValue = null) {
        const value = localStorage.getItem(this.storageKeys[key] || key);
        if (value === null) return defaultValue;
        try {
            return JSON.parse(value);
        } catch (e) {
            return value;
        }
    },
    
    /**
     * Store configuration value
     */
    setSetting: function(key, value) {
        const storageKey = this.storageKeys[key] || key;
        const stringValue = typeof value === 'string' ? value : JSON.stringify(value);
        localStorage.setItem(storageKey, stringValue);
    },
    
    /**
     * Format bytes to human readable format
     */
    formatBytes: function(bytes, decimals = 2) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const dm = decimals < 0 ? 0 : decimals;
        const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
    },
    
    /**
     * Format duration in seconds to human readable format
     */
    formatDuration: function(seconds) {
        if (seconds < 60) return `${seconds}s`;
        if (seconds < 3600) return `${Math.floor(seconds / 60)}m ${seconds % 60}s`;
        if (seconds < 86400) {
            const hours = Math.floor(seconds / 3600);
            const minutes = Math.floor((seconds % 3600) / 60);
            return `${hours}h ${minutes}m`;
        }
        const days = Math.floor(seconds / 86400);
        const hours = Math.floor((seconds % 86400) / 3600);
        return `${days}d ${hours}h`;
    },
    
    /**
     * Get status color
     */
    getStatusColor: function(type, status) {
        const colors = type === 'device' ? this.deviceStatusColors : this.taskStatusColors;
        return colors[status] || '#a0a0a0';
    },
    
    /**
     * Validate input against pattern
     */
    validate: function(input, patternName) {
        const pattern = this.patterns[patternName];
        return pattern ? pattern.test(input) : true;
    },
    
    /**
     * Check if feature is enabled
     */
    isFeatureEnabled: function(featureName) {
        return this.features[featureName] === true;
    },
    
    /**
     * Debounce function
     */
    debounce: function(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    },
    
    /**
     * Throttle function
     */
    throttle: function(func, limit) {
        let inThrottle;
        return function() {
            const args = arguments;
            const context = this;
            if (!inThrottle) {
                func.apply(context, args);
                inThrottle = true;
                setTimeout(() => inThrottle = false, limit);
            }
        };
    }
};

// Bind utils to config object
Object.keys(window.RetireClusterConfig.utils).forEach(key => {
    if (typeof window.RetireClusterConfig.utils[key] === 'function') {
        window.RetireClusterConfig.utils[key] = window.RetireClusterConfig.utils[key].bind(window.RetireClusterConfig);
    }
});

console.log('Retire-Cluster Config loaded successfully');