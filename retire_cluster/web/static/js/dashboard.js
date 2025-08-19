/**
 * Dashboard functionality for Retire-Cluster
 */

class RetireClusterDashboard {
    constructor(api, config) {
        this.api = api;
        this.config = config;
        this.charts = {};
        this.refreshTimers = {};
        this.isInitialized = false;
        
        // Bind methods
        this.init = this.init.bind(this);
        this.updateStats = this.updateStats.bind(this);
        this.updateCharts = this.updateCharts.bind(this);
        this.updateActivity = this.updateActivity.bind(this);
    }

    async init() {
        if (this.isInitialized) return;
        
        console.log('Initializing dashboard...');
        
        try {
            // Initialize charts
            await this.initializeCharts();
            
            // Load initial data
            await this.loadInitialData();
            
            // Start refresh timers
            this.startRefreshTimers();
            
            // Setup event listeners
            this.setupEventListeners();
            
            this.isInitialized = true;
            console.log('Dashboard initialized successfully');
            
        } catch (error) {
            console.error('Failed to initialize dashboard:', error);
            this.showError('Failed to initialize dashboard');
        }
    }

    async loadInitialData() {
        await Promise.all([
            this.updateStats(),
            this.updateCharts(),
            this.updateActivity()
        ]);
    }

    async updateStats() {
        try {
            const [clusterStatus, devices, tasks] = await Promise.all([
                this.api.getClusterStatus(),
                this.api.getDevices(),
                this.api.getTasks()
            ]);

            // Update cluster stats
            this.updateClusterStats(clusterStatus.data || clusterStatus);
            
            // Update device stats
            this.updateDeviceStats(devices.data?.devices || devices);
            
            // Update task stats
            this.updateTaskStats(tasks.data?.tasks || tasks);
            
        } catch (error) {
            console.error('Failed to update stats:', error);
        }
    }

    updateClusterStats(clusterData) {
        const elements = {
            totalDevices: document.getElementById('totalDevices'),
            devicesChange: document.getElementById('devicesChange'),
            totalCores: document.getElementById('totalCores'),
            coreUtilization: document.getElementById('coreUtilization'),
            healthScore: document.getElementById('healthScore')
        };

        if (elements.totalDevices) {
            elements.totalDevices.textContent = clusterData.nodes_total || 0;
        }
        
        if (elements.devicesChange) {
            elements.devicesChange.textContent = clusterData.nodes_online || 0;
        }
        
        if (elements.totalCores) {
            elements.totalCores.textContent = clusterData.cpu_cores || 0;
        }
        
        if (elements.coreUtilization) {
            elements.coreUtilization.textContent = Math.round(clusterData.cpu_usage || 0);
        }
        
        if (elements.healthScore) {
            const healthPercentage = this.calculateHealthScore(clusterData);
            elements.healthScore.textContent = `${healthPercentage}%`;
        }
    }

    updateDeviceStats(devices) {
        const onlineDevices = devices.filter(device => device.status === 'online').length;
        const totalDevices = devices.length;
        
        const totalDevicesEl = document.getElementById('totalDevices');
        const devicesChangeEl = document.getElementById('devicesChange');
        
        if (totalDevicesEl) {
            totalDevicesEl.textContent = totalDevices;
        }
        
        if (devicesChangeEl) {
            devicesChangeEl.textContent = onlineDevices;
        }
    }

    updateTaskStats(tasks) {
        const activeTasks = tasks.filter(task => 
            task.status === 'running' || task.status === 'queued'
        ).length;
        
        const completedTasks = tasks.filter(task => 
            task.status === 'completed'
        ).length;
        
        const activeTasksEl = document.getElementById('activeTasks');
        const tasksCompletedEl = document.getElementById('tasksCompleted');
        
        if (activeTasksEl) {
            activeTasksEl.textContent = activeTasks;
        }
        
        if (tasksCompletedEl) {
            tasksCompletedEl.textContent = completedTasks;
        }
    }

    calculateHealthScore(clusterData) {
        // Simple health calculation based on various factors
        let score = 100;
        
        // Deduct points for high CPU usage
        if (clusterData.cpu_usage > 80) score -= 20;
        else if (clusterData.cpu_usage > 60) score -= 10;
        
        // Deduct points for high memory usage
        if (clusterData.memory_usage > 80) score -= 20;
        else if (clusterData.memory_usage > 60) score -= 10;
        
        // Deduct points for offline nodes
        const nodeRatio = clusterData.nodes_online / clusterData.nodes_total;
        if (nodeRatio < 0.5) score -= 30;
        else if (nodeRatio < 0.8) score -= 15;
        
        return Math.max(0, score);
    }

    async initializeCharts() {
        try {
            // Task execution trend chart
            await this.initTaskChart();
            
            // Device distribution chart
            await this.initDeviceChart();
            
        } catch (error) {
            console.error('Failed to initialize charts:', error);
        }
    }

    async initTaskChart() {
        const ctx = document.getElementById('taskChart');
        if (!ctx) return;

        // Generate sample data for demo
        const now = new Date();
        const labels = [];
        const data = [];
        
        for (let i = 23; i >= 0; i--) {
            const time = new Date(now.getTime() - (i * 60 * 60 * 1000));
            labels.push(time.toLocaleTimeString([], {hour: '2-digit', minute: '2-digit'}));
            data.push(Math.floor(Math.random() * 20) + 5);
        }

        this.charts.taskChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Tasks Executed',
                    data: data,
                    borderColor: this.config.chartColors.primary,
                    backgroundColor: this.config.chartColors.primary + '20',
                    tension: 0.4,
                    fill: true
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        grid: {
                            color: 'rgba(255, 255, 255, 0.1)'
                        },
                        ticks: {
                            color: 'rgba(255, 255, 255, 0.7)'
                        }
                    },
                    x: {
                        grid: {
                            color: 'rgba(255, 255, 255, 0.1)'
                        },
                        ticks: {
                            color: 'rgba(255, 255, 255, 0.7)'
                        }
                    }
                }
            }
        });
    }

    async initDeviceChart() {
        const ctx = document.getElementById('deviceChart');
        if (!ctx) return;

        try {
            const devicesResponse = await this.api.getDevices();
            const devices = devicesResponse.data?.devices || devicesResponse;
            
            // Count devices by platform
            const platformCounts = {};
            devices.forEach(device => {
                const platform = device.platform || 'Unknown';
                platformCounts[platform] = (platformCounts[platform] || 0) + 1;
            });

            const labels = Object.keys(platformCounts);
            const data = Object.values(platformCounts);
            const colors = labels.map((_, index) => {
                const colorKeys = Object.keys(this.config.chartColors);
                return this.config.chartColors[colorKeys[index % colorKeys.length]];
            });

            this.charts.deviceChart = new Chart(ctx, {
                type: 'doughnut',
                data: {
                    labels: labels,
                    datasets: [{
                        data: data,
                        backgroundColor: colors,
                        borderWidth: 2,
                        borderColor: '#1a1a2e'
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            position: 'right',
                            labels: {
                                color: 'rgba(255, 255, 255, 0.8)',
                                padding: 20,
                                usePointStyle: true
                            }
                        }
                    }
                }
            });
        } catch (error) {
            console.error('Failed to initialize device chart:', error);
        }
    }

    async updateCharts() {
        try {
            await this.updateTaskChart();
            await this.updateDeviceChart();
        } catch (error) {
            console.error('Failed to update charts:', error);
        }
    }

    async updateTaskChart() {
        if (!this.charts.taskChart) return;
        
        // In a real implementation, fetch actual task execution data
        // For now, simulate data update
        const data = this.charts.taskChart.data.datasets[0].data;
        data.shift(); // Remove first element
        data.push(Math.floor(Math.random() * 20) + 5); // Add new element
        
        // Update labels
        const labels = this.charts.taskChart.data.labels;
        labels.shift();
        labels.push(new Date().toLocaleTimeString([], {hour: '2-digit', minute: '2-digit'}));
        
        this.charts.taskChart.update();
    }

    async updateDeviceChart() {
        if (!this.charts.deviceChart) return;
        
        try {
            const devicesResponse = await this.api.getDevices();
            const devices = devicesResponse.data?.devices || devicesResponse;
            
            // Recalculate platform distribution
            const platformCounts = {};
            devices.forEach(device => {
                const platform = device.platform || 'Unknown';
                platformCounts[platform] = (platformCounts[platform] || 0) + 1;
            });

            this.charts.deviceChart.data.labels = Object.keys(platformCounts);
            this.charts.deviceChart.data.datasets[0].data = Object.values(platformCounts);
            this.charts.deviceChart.update();
            
        } catch (error) {
            console.error('Failed to update device chart:', error);
        }
    }

    async updateActivity() {
        try {
            // Get recent logs for activity feed
            const logsResponse = await this.api.getLogs({ limit: 10 });
            const logs = logsResponse.data?.logs || logsResponse;
            
            const activityList = document.getElementById('activityList');
            if (!activityList) return;

            // Clear existing activity
            activityList.innerHTML = '';

            // Add recent activities
            logs.forEach(log => {
                const activityItem = this.createActivityItem(log);
                activityList.appendChild(activityItem);
            });

            // If no activities, show placeholder
            if (logs.length === 0) {
                activityList.innerHTML = `
                    <div class="activity-item">
                        <div class="activity-icon">
                            <i class="fas fa-info-circle"></i>
                        </div>
                        <div class="activity-content">
                            <h4>No recent activity</h4>
                            <p>Activities will appear here as they occur</p>
                        </div>
                        <div class="activity-time">--</div>
                    </div>
                `;
            }
            
        } catch (error) {
            console.error('Failed to update activity:', error);
        }
    }

    createActivityItem(log) {
        const item = document.createElement('div');
        item.className = 'activity-item';

        const icon = this.getActivityIcon(log.level || log.type);
        const time = new Date(log.timestamp).toLocaleTimeString([], {
            hour: '2-digit',
            minute: '2-digit'
        });

        item.innerHTML = `
            <div class="activity-icon">
                <i class="fas ${icon}"></i>
            </div>
            <div class="activity-content">
                <h4>${this.formatLogTitle(log)}</h4>
                <p>${log.message || log.description}</p>
            </div>
            <div class="activity-time">${time}</div>
        `;

        return item;
    }

    getActivityIcon(type) {
        const iconMap = {
            'INFO': 'fa-info-circle',
            'WARNING': 'fa-exclamation-triangle',
            'ERROR': 'fa-times-circle',
            'SUCCESS': 'fa-check-circle',
            'device': 'fa-server',
            'task': 'fa-tasks',
            'cluster': 'fa-network-wired'
        };
        
        return iconMap[type] || 'fa-circle';
    }

    formatLogTitle(log) {
        if (log.device) return `Device ${log.device}`;
        if (log.task_id) return `Task ${log.task_id}`;
        return log.source || 'System';
    }

    setupEventListeners() {
        // Chart filter listeners
        const chartFilters = document.querySelectorAll('.chart-filter');
        chartFilters.forEach(filter => {
            filter.addEventListener('change', (e) => {
                this.handleChartFilterChange(e.target);
            });
        });

        // Export button
        const exportBtn = document.querySelector('[onclick="exportData()"]');
        if (exportBtn) {
            exportBtn.removeAttribute('onclick');
            exportBtn.addEventListener('click', () => this.handleExportData());
        }

        // Refresh button
        const refreshBtn = document.getElementById('refreshBtn');
        if (refreshBtn) {
            refreshBtn.addEventListener('click', () => this.handleRefresh());
        }
    }

    handleChartFilterChange(filter) {
        const timeRange = filter.value;
        console.log('Chart filter changed to:', timeRange);
        // Update charts based on time range
        this.updateCharts();
    }

    async handleExportData() {
        try {
            const format = 'json'; // Could be made configurable
            const data = await this.api.exportData('dashboard', format);
            
            // Create download link
            const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `dashboard-export-${new Date().toISOString().split('T')[0]}.json`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
            
            this.showSuccess('Dashboard data exported successfully');
            
        } catch (error) {
            console.error('Export failed:', error);
            this.showError('Failed to export data');
        }
    }

    handleRefresh() {
        console.log('Refreshing dashboard...');
        this.loadInitialData();
    }

    startRefreshTimers() {
        // Stats refresh
        this.refreshTimers.stats = setInterval(() => {
            this.updateStats();
        }, this.config.refreshInterval);

        // Charts refresh
        this.refreshTimers.charts = setInterval(() => {
            this.updateCharts();
        }, this.config.refreshInterval * 2);

        // Activity refresh
        this.refreshTimers.activity = setInterval(() => {
            this.updateActivity();
        }, this.config.refreshInterval);
    }

    stopRefreshTimers() {
        Object.values(this.refreshTimers).forEach(timer => {
            if (timer) clearInterval(timer);
        });
        this.refreshTimers = {};
    }

    showSuccess(message) {
        this.showNotification(message, 'success');
    }

    showError(message) {
        this.showNotification(message, 'error');
    }

    showNotification(message, type = 'info') {
        if (!this.config.enableNotifications) return;

        const toast = document.getElementById('toast');
        if (!toast) return;

        const icon = toast.querySelector('.toast-icon');
        const messageEl = toast.querySelector('.toast-message');

        // Set content
        messageEl.textContent = message;
        
        // Set type
        toast.className = `toast ${type}`;
        
        // Update icon
        const iconMap = {
            success: 'fa-check-circle',
            error: 'fa-times-circle',
            warning: 'fa-exclamation-triangle',
            info: 'fa-info-circle'
        };
        icon.className = `toast-icon fas ${iconMap[type]}`;

        // Show toast
        toast.classList.add('show');

        // Hide after 3 seconds
        setTimeout(() => {
            toast.classList.remove('show');
        }, 3000);
    }

    destroy() {
        this.stopRefreshTimers();
        
        // Destroy charts
        Object.values(this.charts).forEach(chart => {
            if (chart && typeof chart.destroy === 'function') {
                chart.destroy();
            }
        });
        
        this.isInitialized = false;
    }
}

// Create global dashboard instance
window.dashboard = new RetireClusterDashboard(window.api, window.RetireClusterConfig);

// Export functions that may be called from HTML
window.exportData = () => window.dashboard.handleExportData();

console.log('Retire-Cluster Dashboard loaded successfully');