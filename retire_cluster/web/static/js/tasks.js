/**
 * Task management functionality for Retire-Cluster
 */

class TaskManager {
    constructor(api, config) {
        this.api = api;
        this.config = config;
        this.tasks = [];
        this.filteredTasks = [];
        this.currentFilter = 'all';
        this.sortBy = 'created';
        this.sortOrder = 'desc';
        
        this.init = this.init.bind(this);
        this.loadTasks = this.loadTasks.bind(this);
        this.filterTasks = this.filterTasks.bind(this);
        this.renderTasks = this.renderTasks.bind(this);
    }

    async init() {
        console.log('Initializing task manager...');
        
        try {
            await this.loadTasks();
            this.setupEventListeners();
            this.startAutoRefresh();
            console.log('Task manager initialized successfully');
        } catch (error) {
            console.error('Failed to initialize task manager:', error);
        }
    }

    async loadTasks() {
        try {
            const response = await this.api.getTasks();
            this.tasks = response.data?.tasks || response;
            this.filterTasks();
            this.renderTasks();
        } catch (error) {
            console.error('Failed to load tasks:', error);
            this.showError('Failed to load tasks');
        }
    }

    filterTasks() {
        this.filteredTasks = this.tasks.filter(task => {
            if (this.currentFilter === 'all') return true;
            return task.status === this.currentFilter;
        });
        
        // Sort tasks
        this.filteredTasks.sort((a, b) => {
            let aVal = a[this.sortBy];
            let bVal = b[this.sortBy];
            
            // Handle different data types
            if (this.sortBy === 'created' || this.sortBy === 'updated') {
                aVal = new Date(aVal);
                bVal = new Date(bVal);
            }
            
            if (this.sortBy === 'priority') {
                aVal = this.config.taskPriorities[aVal]?.weight || 0;
                bVal = this.config.taskPriorities[bVal]?.weight || 0;
            }
            
            if (this.sortOrder === 'asc') {
                return aVal > bVal ? 1 : -1;
            } else {
                return aVal < bVal ? 1 : -1;
            }
        });
    }

    renderTasks() {
        const tbody = document.getElementById('tasksTableBody');
        if (!tbody) return;

        tbody.innerHTML = '';

        if (this.filteredTasks.length === 0) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="8" class="text-center" style="padding: 2rem;">
                        <i class="fas fa-tasks" style="font-size: 2rem; color: var(--text-muted); margin-bottom: 1rem; display: block;"></i>
                        <h4>No tasks found</h4>
                        <p>Try adjusting your filter or submit a new task.</p>
                    </td>
                </tr>
            `;
            return;
        }

        this.filteredTasks.forEach(task => {
            const row = this.createTaskRow(task);
            tbody.appendChild(row);
        });
    }

    createTaskRow(task) {
        const row = document.createElement('tr');
        row.onclick = () => this.showTaskDetails(task);
        row.style.cursor = 'pointer';

        const createdDate = task.created ? new Date(task.created).toLocaleString() : 'N/A';
        const duration = this.calculateDuration(task);
        const statusClass = task.status || 'unknown';
        const priorityClass = task.priority || 'normal';

        row.innerHTML = `
            <td>
                <code class="task-id">${task.id || 'N/A'}</code>
            </td>
            <td>
                <span class="task-type">
                    <i class="fas ${this.getTaskTypeIcon(task.type)}"></i>
                    ${task.type || 'Unknown'}
                </span>
            </td>
            <td>
                <span class="task-status ${statusClass}">${statusClass}</span>
            </td>
            <td>
                <span class="priority-badge priority-${priorityClass}">${priorityClass}</span>
            </td>
            <td>
                <span class="device-name">
                    <i class="fas fa-server"></i>
                    ${task.device_id || 'Unassigned'}
                </span>
            </td>
            <td>
                <span class="task-created">${createdDate}</span>
            </td>
            <td>
                <span class="task-duration">${duration}</span>
            </td>
            <td>
                <div class="task-actions">
                    <button class="btn btn-sm btn-secondary" 
                            onclick="event.stopPropagation(); window.taskManager.viewTaskResult('${task.id}')" 
                            title="View Result">
                        <i class="fas fa-eye"></i>
                    </button>
                    ${task.status === 'running' ? `
                        <button class="btn btn-sm btn-warning" 
                                onclick="event.stopPropagation(); window.taskManager.cancelTask('${task.id}')" 
                                title="Cancel Task">
                            <i class="fas fa-stop"></i>
                        </button>
                    ` : ''}
                    <button class="btn btn-sm btn-info" 
                            onclick="event.stopPropagation(); window.taskManager.viewTaskLogs('${task.id}')" 
                            title="View Logs">
                        <i class="fas fa-file-alt"></i>
                    </button>
                </div>
            </td>
        `;

        return row;
    }

    getTaskTypeIcon(type) {
        const iconMap = {
            'echo': 'fa-comment',
            'sleep': 'fa-bed',
            'system_info': 'fa-info-circle',
            'python_eval': 'fa-code',
            'http_request': 'fa-globe',
            'command': 'fa-terminal',
            'shell_command': 'fa-terminal'
        };
        return iconMap[type] || 'fa-cog';
    }

    calculateDuration(task) {
        if (!task.created) return 'N/A';
        
        const start = new Date(task.created);
        let end = new Date();
        
        if (task.completed) {
            end = new Date(task.completed);
        }
        
        const durationMs = end - start;
        const seconds = Math.floor(durationMs / 1000);
        
        return this.config.utils.formatDuration(seconds);
    }

    setupEventListeners() {
        // Filter dropdown
        const taskFilter = document.getElementById('taskFilter');
        if (taskFilter) {
            taskFilter.addEventListener('change', (e) => {
                this.currentFilter = e.target.value;
                this.filterTasks();
                this.renderTasks();
            });
        }

        // Table headers for sorting
        const headers = document.querySelectorAll('#tasksTable th[data-sort]');
        headers.forEach(header => {
            header.style.cursor = 'pointer';
            header.addEventListener('click', () => {
                const sortBy = header.dataset.sort;
                if (this.sortBy === sortBy) {
                    this.sortOrder = this.sortOrder === 'asc' ? 'desc' : 'asc';
                } else {
                    this.sortBy = sortBy;
                    this.sortOrder = 'desc';
                }
                this.filterTasks();
                this.renderTasks();
                this.updateSortIndicators();
            });
        });
    }

    updateSortIndicators() {
        // Remove existing sort indicators
        document.querySelectorAll('.sort-indicator').forEach(el => el.remove());
        
        // Add current sort indicator
        const currentHeader = document.querySelector(`#tasksTable th[data-sort="${this.sortBy}"]`);
        if (currentHeader) {
            const indicator = document.createElement('i');
            indicator.className = `fas fa-sort-${this.sortOrder === 'asc' ? 'up' : 'down'} sort-indicator`;
            indicator.style.marginLeft = '5px';
            currentHeader.appendChild(indicator);
        }
    }

    async showTaskDetails(task) {
        try {
            const taskDetails = await this.api.getTask(task.id);
            const taskData = taskDetails.data || taskDetails;
            console.log('Task details:', taskData);
            // Could show task details in a modal
            this.showNotification(`Viewing details for task ${task.id}`, 'info');
        } catch (error) {
            console.error('Failed to get task details:', error);
            this.showError('Failed to load task details');
        }
    }

    async viewTaskResult(taskId) {
        try {
            const result = await this.api.getTaskResult(taskId);
            console.log('Task result:', result);
            // Could show result in a modal or new page
            this.showNotification(`Viewing result for task ${taskId}`, 'info');
        } catch (error) {
            console.error('Failed to get task result:', error);
            this.showError('Failed to load task result');
        }
    }

    async viewTaskLogs(taskId) {
        try {
            const logs = await this.api.getTaskLogs(taskId);
            console.log('Task logs:', logs);
            // Could show logs in a modal
            this.showNotification(`Viewing logs for task ${taskId}`, 'info');
        } catch (error) {
            console.error('Failed to get task logs:', error);
            this.showError('Failed to load task logs');
        }
    }

    async cancelTask(taskId) {
        if (!confirm(`Are you sure you want to cancel task ${taskId}?`)) {
            return;
        }

        try {
            await this.api.cancelTask(taskId);
            this.showSuccess(`Task ${taskId} cancelled successfully`);
            await this.loadTasks();
        } catch (error) {
            console.error('Failed to cancel task:', error);
            this.showError('Failed to cancel task');
        }
    }

    async submitTask(taskData) {
        try {
            const result = await this.api.submitTask(taskData);
            this.showSuccess('Task submitted successfully');
            await this.loadTasks();
            this.closeModal('submitTaskModal');
            return result;
        } catch (error) {
            console.error('Failed to submit task:', error);
            this.showError('Failed to submit task');
            throw error;
        }
    }

    showSubmitTaskModal() {
        const modal = document.getElementById('submitTaskModal');
        if (modal) {
            modal.classList.add('active');
            // Reset form
            const form = document.getElementById('submitTaskForm');
            if (form) form.reset();
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

    startAutoRefresh() {
        if (this.refreshTimer) {
            clearInterval(this.refreshTimer);
        }
        
        this.refreshTimer = setInterval(() => {
            this.loadTasks();
        }, this.config.taskRefreshInterval);
    }

    stopAutoRefresh() {
        if (this.refreshTimer) {
            clearInterval(this.refreshTimer);
            this.refreshTimer = null;
        }
    }
}

// Create global task manager instance
window.taskManager = new TaskManager(window.api, window.RetireClusterConfig);

// Export functions that may be called from HTML
window.showSubmitTaskModal = () => {
    window.taskManager.showSubmitTaskModal();
};

window.submitTask = async () => {
    const form = document.getElementById('submitTaskForm');
    if (!form || !form.checkValidity()) {
        form.reportValidity();
        return;
    }

    try {
        const formData = new FormData(form);
        const taskData = {
            type: document.getElementById('taskType').value,
            priority: document.getElementById('taskPriority').value,
            payload: JSON.parse(document.getElementById('taskPayload').value),
            requirements: {}
        };

        // Add requirements if specified
        const minCpu = document.getElementById('minCpu').value;
        const minMemory = document.getElementById('minMemory').value;
        const requiredPlatform = document.getElementById('requiredPlatform').value;

        if (minCpu) taskData.requirements.min_cpu_cores = parseInt(minCpu);
        if (minMemory) taskData.requirements.min_memory_gb = parseInt(minMemory);
        if (requiredPlatform) taskData.requirements.required_platform = requiredPlatform;

        await window.taskManager.submitTask(taskData);
    } catch (error) {
        if (error.name === 'SyntaxError') {
            window.taskManager.showError('Invalid JSON in payload field');
        } else {
            window.taskManager.showError('Failed to submit task');
        }
    }
};

window.closeModal = (modalId) => {
    window.taskManager.closeModal(modalId);
};

console.log('Task Manager loaded successfully');