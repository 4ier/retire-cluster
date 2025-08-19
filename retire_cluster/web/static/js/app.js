/**
 * Main application controller for Retire-Cluster Dashboard
 */

class RetireClusterApp {
    constructor() {
        this.currentPage = 'dashboard';
        this.isInitialized = false;
        this.managers = {};
        this.theme = localStorage.getItem('theme') || 'dark';
        
        // Bind methods
        this.init = this.init.bind(this);
        this.switchPage = this.switchPage.bind(this);
        this.toggleTheme = this.toggleTheme.bind(this);
        this.handleKeyboardShortcuts = this.handleKeyboardShortcuts.bind(this);
    }

    async init() {
        if (this.isInitialized) return;
        
        console.log('Initializing Retire-Cluster Dashboard...');
        
        try {
            // Apply saved theme
            this.applyTheme(this.theme);
            
            // Setup global event listeners
            this.setupGlobalEventListeners();
            
            // Check API connectivity
            await this.checkApiConnectivity();
            
            // Initialize page managers
            await this.initializeManagers();
            
            // Setup navigation
            this.setupNavigation();
            
            // Initialize the current page
            await this.switchPage(this.currentPage);
            
            // Setup refresh functionality
            this.setupRefreshButton();
            
            // Setup connection monitoring
            this.startConnectionMonitoring();
            
            this.isInitialized = true;
            console.log('Dashboard initialized successfully');
            
            // Show welcome notification
            this.showWelcome();
            
        } catch (error) {
            console.error('Failed to initialize dashboard:', error);
            this.showError('Failed to initialize dashboard. Please check your connection.');
        }
    }

    async checkApiConnectivity() {
        const isConnected = await window.api.healthCheck();
        if (!isConnected) {
            throw new Error('Cannot connect to API server');
        }
        
        this.updateConnectionStatus(true);
    }

    async initializeManagers() {
        // Dashboard manager (already created globally)
        this.managers.dashboard = window.dashboard;
        
        // Device manager (already created globally)
        this.managers.devices = window.deviceManager;
        
        // Task manager (already created globally)
        this.managers.tasks = window.taskManager;
    }

    setupGlobalEventListeners() {
        // Theme toggle
        const themeToggle = document.getElementById('themeToggle');
        if (themeToggle) {
            themeToggle.addEventListener('click', this.toggleTheme);
        }
        
        // Keyboard shortcuts
        document.addEventListener('keydown', this.handleKeyboardShortcuts);
        
        // Modal close events
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('modal')) {
                e.target.classList.remove('active');
            }
        });
        
        // Escape key to close modals
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                const activeModal = document.querySelector('.modal.active');
                if (activeModal) {
                    activeModal.classList.remove('active');
                }
            }
        });
        
        // Window beforeunload to cleanup
        window.addEventListener('beforeunload', () => {
            this.cleanup();
        });
    }

    setupNavigation() {
        const navLinks = document.querySelectorAll('.nav-link');
        navLinks.forEach(link => {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                const page = link.dataset.page;
                if (page) {
                    this.switchPage(page);
                }
            });
        });
    }

    async switchPage(pageName) {
        if (pageName === this.currentPage) return;
        
        console.log(`Switching to page: ${pageName}`);
        
        // Hide all pages
        document.querySelectorAll('.page').forEach(page => {
            page.classList.remove('active');
        });
        
        // Show target page
        const targetPage = document.getElementById(pageName);
        if (targetPage) {
            targetPage.classList.add('active');
        }
        
        // Update navigation
        document.querySelectorAll('.nav-link').forEach(link => {
            link.classList.remove('active');
        });
        
        const activeNavLink = document.querySelector(`[data-page="${pageName}"]`);
        if (activeNavLink) {
            activeNavLink.classList.add('active');
        }
        
        // Initialize page-specific functionality
        try {
            switch (pageName) {
                case 'dashboard':
                    if (this.managers.dashboard && !this.managers.dashboard.isInitialized) {
                        await this.managers.dashboard.init();
                    }
                    break;
                    
                case 'devices':
                    if (this.managers.devices) {
                        await this.managers.devices.init();
                        this.managers.devices.startAutoRefresh();
                    }
                    break;
                    
                case 'tasks':
                    if (this.managers.tasks) {
                        await this.managers.tasks.init();
                    }
                    break;
                    
                case 'settings':
                    this.loadSettings();
                    break;
            }
        } catch (error) {
            console.error(`Failed to initialize page ${pageName}:`, error);
            this.showError(`Failed to load ${pageName} page`);
        }
        
        // Stop auto-refresh for pages that are no longer active
        if (this.currentPage === 'devices' && pageName !== 'devices') {
            this.managers.devices?.stopAutoRefresh();
        }
        
        this.currentPage = pageName;
        
        // Update URL hash
        window.location.hash = `#${pageName}`;
    }

    handleKeyboardShortcuts(e) {
        // Ctrl/Cmd + number keys for quick page switching
        if ((e.ctrlKey || e.metaKey) && e.key >= '1' && e.key <= '4') {
            e.preventDefault();
            const pages = ['dashboard', 'devices', 'tasks', 'settings'];
            const pageIndex = parseInt(e.key) - 1;
            if (pages[pageIndex]) {
                this.switchPage(pages[pageIndex]);
            }
        }
        
        // Ctrl/Cmd + R for refresh
        if ((e.ctrlKey || e.metaKey) && e.key === 'r') {
            e.preventDefault();
            this.refreshCurrentPage();
        }
        
        // F5 for refresh
        if (e.key === 'F5') {
            e.preventDefault();
            this.refreshCurrentPage();
        }
    }

    async refreshCurrentPage() {
        console.log(`Refreshing ${this.currentPage} page...`);
        
        try {
            switch (this.currentPage) {
                case 'dashboard':
                    if (this.managers.dashboard) {
                        await this.managers.dashboard.loadInitialData();
                    }
                    break;
                    
                case 'devices':
                    if (this.managers.devices) {
                        await this.managers.devices.loadDevices();
                    }
                    break;
                    
                case 'tasks':
                    if (this.managers.tasks) {
                        await this.managers.tasks.loadTasks();
                    }
                    break;
            }
            
            this.showNotification(`${this.currentPage} page refreshed`, 'success');
        } catch (error) {
            console.error('Refresh failed:', error);
            this.showError('Failed to refresh page');
        }
    }

    setupRefreshButton() {
        const refreshBtn = document.getElementById('refreshBtn');
        if (refreshBtn) {
            refreshBtn.addEventListener('click', () => {
                this.refreshCurrentPage();
                
                // Visual feedback
                refreshBtn.style.transform = 'rotate(180deg)';
                setTimeout(() => {
                    refreshBtn.style.transform = '';
                }, 300);
            });
        }
    }

    toggleTheme() {
        const newTheme = this.theme === 'dark' ? 'light' : 'dark';
        this.applyTheme(newTheme);
        this.theme = newTheme;
        localStorage.setItem('theme', newTheme);
        
        this.showNotification(`Switched to ${newTheme} theme`, 'info');
    }

    applyTheme(theme) {
        document.body.classList.remove('theme-light', 'theme-dark');
        document.body.classList.add(`theme-${theme}`);
        
        const themeIcon = document.querySelector('#themeToggle i');
        if (themeIcon) {
            themeIcon.className = theme === 'dark' ? 'fas fa-sun' : 'fas fa-moon';
        }
    }

    loadSettings() {
        // Load settings from config
        const config = window.RetireClusterConfig;
        
        // API Settings
        const apiUrlInput = document.getElementById('apiUrl');
        if (apiUrlInput) {
            apiUrlInput.value = config.apiBaseUrl;
        }
        
        const apiKeyInput = document.getElementById('apiKey');
        if (apiKeyInput && window.api.apiKey) {
            apiKeyInput.value = '••••••••';
        }
        
        const refreshIntervalInput = document.getElementById('refreshInterval');
        if (refreshIntervalInput) {
            refreshIntervalInput.value = config.refreshInterval / 1000;
        }
        
        // Display Settings
        const enableNotifications = document.getElementById('enableNotifications');
        if (enableNotifications) {
            enableNotifications.checked = config.enableNotifications;
        }
        
        const enableSound = document.getElementById('enableSound');
        if (enableSound) {
            enableSound.checked = config.enableSound;
        }
        
        const autoRefresh = document.getElementById('autoRefresh');
        if (autoRefresh) {
            autoRefresh.checked = config.autoRefresh;
        }
        
        const themeSelect = document.getElementById('themeSelect');
        if (themeSelect) {
            themeSelect.value = this.theme;
        }
        
        // Load API version
        this.loadApiVersion();
    }

    async loadApiVersion() {
        try {
            const systemInfo = await window.api.getSystemInfo();
            const apiVersionEl = document.getElementById('apiVersion');
            if (apiVersionEl) {
                apiVersionEl.textContent = systemInfo.version || '1.1.0';
            }
        } catch (error) {
            const apiVersionEl = document.getElementById('apiVersion');
            if (apiVersionEl) {
                apiVersionEl.textContent = 'Unknown';
            }
        }
    }

    updateConnectionStatus(isConnected) {
        const indicator = document.getElementById('connectionStatus');
        const statusText = document.querySelector('.connection-status .status-text');
        
        if (indicator) {
            indicator.className = `status-indicator ${isConnected ? 'online pulse' : 'offline'}`;
        }
        
        if (statusText) {
            statusText.textContent = isConnected ? 'Connected' : 'Disconnected';
        }
    }

    startConnectionMonitoring() {
        // Check connection every 30 seconds
        setInterval(async () => {
            const isConnected = await window.api.healthCheck();
            this.updateConnectionStatus(isConnected);
            
            if (!isConnected) {
                this.showError('Lost connection to server', false);
            }
        }, 30000);
    }

    showWelcome() {
        const welcomeMessages = [
            'Welcome to Retire-Cluster Dashboard! 🚀',
            'Dashboard loaded successfully ✅',
            'All systems operational 💚'
        ];
        
        const message = welcomeMessages[Math.floor(Math.random() * welcomeMessages.length)];
        
        setTimeout(() => {
            this.showNotification(message, 'success');
        }, 1000);
    }

    showNotification(message, type = 'info', autoHide = true) {
        if (this.managers.dashboard) {
            this.managers.dashboard.showNotification(message, type);
        } else {
            console.log(`${type.toUpperCase()}: ${message}`);
        }
    }

    showError(message, autoHide = true) {
        this.showNotification(message, 'error', autoHide);
    }

    showSuccess(message) {
        this.showNotification(message, 'success');
    }

    cleanup() {
        console.log('Cleaning up application...');
        
        // Stop all auto-refresh timers
        if (this.managers.dashboard) {
            this.managers.dashboard.stopRefreshTimers();
        }
        
        if (this.managers.devices) {
            this.managers.devices.stopAutoRefresh();
        }
        
        if (this.managers.tasks) {
            this.managers.tasks.stopAutoRefresh();
        }
    }

    // Utility method for handling URL hash navigation
    handleHashChange() {
        const hash = window.location.hash.slice(1);
        const validPages = ['dashboard', 'devices', 'tasks', 'settings'];
        
        if (hash && validPages.includes(hash)) {
            this.switchPage(hash);
        }
    }
}

// Global functions for HTML onclick handlers
window.saveSettings = () => {
    const config = window.RetireClusterConfig;
    
    // Save API settings
    const refreshInterval = parseInt(document.getElementById('refreshInterval').value) * 1000;
    config.refreshInterval = refreshInterval;
    config.utils.setSetting('refreshInterval', refreshInterval);
    
    // Save display preferences
    const enableNotifications = document.getElementById('enableNotifications').checked;
    config.enableNotifications = enableNotifications;
    config.utils.setSetting('enableNotifications', enableNotifications);
    
    const enableSound = document.getElementById('enableSound').checked;
    config.enableSound = enableSound;
    config.utils.setSetting('enableSound', enableSound);
    
    const autoRefresh = document.getElementById('autoRefresh').checked;
    config.autoRefresh = autoRefresh;
    config.utils.setSetting('autoRefresh', autoRefresh);
    
    const theme = document.getElementById('themeSelect').value;
    window.app.applyTheme(theme);
    window.app.theme = theme;
    localStorage.setItem('theme', theme);
    
    // Save API key if provided
    const apiKey = document.getElementById('apiKey').value;
    if (apiKey && apiKey !== '••••••••') {
        window.api.setApiKey(apiKey);
    }
    
    window.app.showSuccess('Settings saved successfully');
};

// Initialize app when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    // Create global app instance
    window.app = new RetireClusterApp();
    
    // Handle hash navigation
    window.addEventListener('hashchange', () => {
        window.app.handleHashChange();
    });
    
    // Check initial hash
    window.app.handleHashChange();
    
    // Initialize the application
    window.app.init().catch(error => {
        console.error('Failed to initialize application:', error);
    });
});

console.log('Retire-Cluster App loaded successfully');