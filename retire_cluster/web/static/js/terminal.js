/**
 * Terminal.js - xterm.js integration for Retire-Cluster
 */

class RetireClusterTerminal {
    constructor() {
        this.term = null;
        this.socket = null;
        this.commandHistory = [];
        this.historyIndex = -1;
        this.currentCommand = '';
        this.commandBuffer = '';
        this.isConnected = false;
        this.apiBaseUrl = window.location.origin;
        
        // Initialize terminal
        this.init();
    }
    
    init() {
        // Create xterm.js terminal
        this.term = new Terminal({
            theme: {
                background: '#0c0c0c',
                foreground: '#00ff00',
                cursor: '#00ff00',
                cursorAccent: '#0c0c0c',
                selection: 'rgba(0, 255, 0, 0.3)',
                black: '#000000',
                red: '#ff0000',
                green: '#00ff00',
                yellow: '#ffff00',
                blue: '#0088ff',
                magenta: '#ff00ff',
                cyan: '#00ffff',
                white: '#ffffff',
                brightBlack: '#808080',
                brightRed: '#ff8080',
                brightGreen: '#80ff80',
                brightYellow: '#ffff80',
                brightBlue: '#8080ff',
                brightMagenta: '#ff80ff',
                brightCyan: '#80ffff',
                brightWhite: '#ffffff'
            },
            fontSize: 14,
            fontFamily: '"Courier New", "Monaco", "Menlo", monospace',
            cursorBlink: true,
            cursorStyle: 'block',
            scrollback: 10000,
            tabStopWidth: 4,
            bell: 'none',
            convertEol: true,
            screenKeys: true,
            useStyle: true,
            lineHeight: 1.2,
            letterSpacing: 0,
            fontWeight: 'normal',
            fontWeightBold: 'bold'
        });
        
        // Create fit addon
        this.fitAddon = new FitAddon.FitAddon();
        this.term.loadAddon(this.fitAddon);
        
        // Open terminal
        this.term.open(document.getElementById('terminal'));
        
        // Fit terminal to container with slight delay to ensure proper sizing
        setTimeout(() => {
            this.fitAddon.fit();
        }, 50);
        
        // Setup event handlers
        this.setupEventHandlers();
        
        // Show welcome message
        this.showWelcome();
        
        // Show initial prompt
        this.showPrompt();
        
        // Connect to status updates
        this.connectStatusUpdates();
        
        // Focus terminal
        this.term.focus();
    }
    
    setupEventHandlers() {
        // Handle keyboard input
        this.term.onData((data) => {
            this.handleInput(data);
        });
        
        // Handle window resize with debounce
        let resizeTimeout;
        window.addEventListener('resize', () => {
            clearTimeout(resizeTimeout);
            resizeTimeout = setTimeout(() => {
                if (this.fitAddon) {
                    this.fitAddon.fit();
                }
            }, 100);
        });
        
        // Handle special key combinations
        this.term.onKey((event) => {
            const { key, domEvent } = event;
            
            // Ctrl+C - Cancel current command
            if (domEvent.ctrlKey && domEvent.key === 'c') {
                this.cancelCommand();
                return;
            }
            
            // Ctrl+L - Clear screen
            if (domEvent.ctrlKey && domEvent.key === 'l') {
                this.clearScreen();
                return;
            }
            
            // Ctrl+R - Reverse search history
            if (domEvent.ctrlKey && domEvent.key === 'r') {
                this.showHistorySearch();
                return;
            }
        });
        
        // Handle copy/paste
        document.addEventListener('paste', (event) => {
            if (document.activeElement === this.term.textarea) {
                const paste = event.clipboardData.getData('text');
                this.term.write(paste);
                this.commandBuffer += paste;
            }
        });
    }
    
    showWelcome() {
        // Clear screen first
        this.term.write('\x1b[2J\x1b[H');
        
        // Write welcome message with proper line endings
        this.term.write('\r\n');
        this.term.write('\x1b[32m╔══════════════════════════════════════════════════════════════════╗\x1b[0m\r\n');
        this.term.write('\x1b[32m║                     RETIRE-CLUSTER v1.1.0                       ║\x1b[0m\r\n');
        this.term.write('\x1b[32m║            CLI-First Distributed Computing Platform             ║\x1b[0m\r\n');
        this.term.write('\x1b[32m╚══════════════════════════════════════════════════════════════════╝\x1b[0m\r\n');
        this.term.write('\r\n');
        this.term.write('\x1b[36mWelcome to the Retire-Cluster terminal interface!\x1b[0m\r\n');
        this.term.write('\r\n');
        this.term.write('Type \'\x1b[33mhelp\x1b[0m\' for available commands or \'\x1b[33mtab\x1b[0m\' for auto-completion.\r\n');
        this.term.write('Use \'\x1b[33mmonitor\x1b[0m\' to start real-time monitoring.\r\n');
        this.term.write('\r\n');
    }
    
    showPrompt() {
        this.term.write('\r\n\x1b[36mcluster@main\x1b[0m:\x1b[34m~\x1b[0m$ ');
        this.commandBuffer = '';
    }
    
    handleInput(data) {
        const code = data.charCodeAt(0);
        
        switch (code) {
            case 13: // Enter
                this.executeCommand();
                break;
                
            case 127: // Backspace
                if (this.commandBuffer.length > 0) {
                    this.commandBuffer = this.commandBuffer.slice(0, -1);
                    this.term.write('\b \b');
                }
                break;
                
            case 9: // Tab
                this.handleTabCompletion();
                break;
                
            case 27: // Escape sequences (arrow keys, etc.)
                // Handle in next character
                break;
                
            default:
                if (data === '\x1b[A') { // Up arrow
                    this.navigateHistory(-1);
                } else if (data === '\x1b[B') { // Down arrow
                    this.navigateHistory(1);
                } else if (data === '\x1b[C') { // Right arrow
                    // Handle cursor movement if needed
                } else if (data === '\x1b[D') { // Left arrow
                    // Handle cursor movement if needed
                } else if (code >= 32 && code <= 126) { // Printable characters
                    this.commandBuffer += data;
                    this.term.write(data);
                }
                break;
        }
    }
    
    async executeCommand() {
        const command = this.commandBuffer.trim();
        
        if (command === '') {
            this.showPrompt();
            return;
        }
        
        // Add to history
        if (command !== this.commandHistory[this.commandHistory.length - 1]) {
            this.commandHistory.push(command);
            if (this.commandHistory.length > 1000) {
                this.commandHistory.shift();
            }
        }
        this.historyIndex = this.commandHistory.length;
        
        this.term.write('\r\n');
        
        try {
            // Show loading indicator
            this.showLoading();
            
            // Execute command via API
            const response = await fetch(`${this.apiBaseUrl}/api/v1/command`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    command: command,
                    format: 'text'
                })
            });
            
            this.hideLoading();
            
            const result = await response.json();
            
            if (result.status === 'success') {
                // Handle special actions
                if (result.action === 'clear') {
                    this.clearScreen();
                    return;
                }
                
                if (result.action === 'exit') {
                    this.showExitMessage();
                    return;
                }
                
                if (result.action === 'monitor') {
                    this.startMonitoring(result.target, result.options);
                    return;
                }
                
                // Display command output
                if (result.output) {
                    this.displayOutput(result.output);
                }
            } else {
                // Display error
                this.displayError(result.message || 'Command failed');
            }
        } catch (error) {
            this.hideLoading();
            this.displayError(`Network error: ${error.message}`);
        }
        
        this.showPrompt();
    }
    
    displayOutput(output) {
        // Parse and colorize output
        const lines = output.split('\n');
        
        for (const line of lines) {
            if (line.trim() === '') {
                this.term.write('\r\n');
                continue;
            }
            
            // Apply syntax highlighting based on content
            let coloredLine = this.colorizeOutput(line);
            this.term.write(coloredLine + '\r\n');
        }
    }
    
    colorizeOutput(line) {
        // Color status indicators
        line = line.replace(/\bonline\b/g, '\x1b[32monline\x1b[0m');
        line = line.replace(/\boffline\b/g, '\x1b[31moffline\x1b[0m');
        line = line.replace(/\bwarning\b/g, '\x1b[33mwarning\x1b[0m');
        line = line.replace(/\berror\b/g, '\x1b[31merror\x1b[0m');
        line = line.replace(/\bhealthy\b/g, '\x1b[32mhealthy\x1b[0m');
        line = line.replace(/\bHEALTHY\b/g, '\x1b[32mHEALTHY\x1b[0m');
        
        // Color numbers and percentages
        line = line.replace(/\b(\d+)%/g, '\x1b[36m$1%\x1b[0m');
        line = line.replace(/\b(\d+\.\d+)GB/g, '\x1b[35m$1GB\x1b[0m');
        
        // Color device IDs
        line = line.replace(/\b([a-z]+-\d+)\b/g, '\x1b[33m$1\x1b[0m');
        
        // Color table separators
        line = line.replace(/─+/g, '\x1b[90m$&\x1b[0m');
        
        return line;
    }
    
    displayError(message) {
        this.term.write(`\x1b[31mError: ${message}\x1b[0m\r\n`);
    }
    
    showLoading() {
        this.term.write('\x1b[36m⟳ Executing...\x1b[0m');
    }
    
    hideLoading() {
        // Clear the loading message
        this.term.write('\r\x1b[K');
    }
    
    cancelCommand() {
        this.commandBuffer = '';
        this.term.write('\r\n\x1b[31m^C\x1b[0m');
        this.showPrompt();
    }
    
    clearScreen() {
        this.term.clear();
        this.showWelcome();
        this.showPrompt();
    }
    
    navigateHistory(direction) {
        if (this.commandHistory.length === 0) return;
        
        if (direction === -1 && this.historyIndex > 0) {
            this.historyIndex--;
        } else if (direction === 1 && this.historyIndex < this.commandHistory.length) {
            this.historyIndex++;
        } else {
            return;
        }
        
        // Clear current command
        for (let i = 0; i < this.commandBuffer.length; i++) {
            this.term.write('\b \b');
        }
        
        // Show history command or empty
        if (this.historyIndex < this.commandHistory.length) {
            this.commandBuffer = this.commandHistory[this.historyIndex];
            this.term.write(this.commandBuffer);
        } else {
            this.commandBuffer = '';
        }
    }
    
    async handleTabCompletion() {
        try {
            const response = await fetch(`${this.apiBaseUrl}/api/v1/suggest`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    partial: this.commandBuffer
                })
            });
            
            if (response.ok) {
                const suggestions = await response.json();
                
                if (suggestions.length === 1) {
                    // Single suggestion - auto-complete
                    const completion = suggestions[0].replace(this.commandBuffer, '');
                    this.commandBuffer += completion;
                    this.term.write(completion);
                } else if (suggestions.length > 1) {
                    // Multiple suggestions - show list
                    this.showSuggestions(suggestions);
                }
            }
        } catch (error) {
            // Tab completion failed - ignore silently
        }
    }
    
    showSuggestions(suggestions) {
        this.term.write('\r\n');
        
        const maxCols = Math.floor(this.term.cols / 20);
        let col = 0;
        
        for (const suggestion of suggestions) {
            this.term.write(`\x1b[36m${suggestion.padEnd(18)}\x1b[0m  `);
            col++;
            
            if (col >= maxCols) {
                this.term.write('\r\n');
                col = 0;
            }
        }
        
        if (col > 0) {
            this.term.write('\r\n');
        }
        
        this.showPrompt();
        this.term.write(this.commandBuffer);
    }
    
    showHistorySearch() {
        // TODO: Implement reverse search
        this.term.write('\r\n\x1b[33mReverse search not implemented yet\x1b[0m');
        this.showPrompt();
    }
    
    showExitMessage() {
        this.term.write('\r\n\x1b[36mGoodbye! Thanks for using Retire-Cluster.\x1b[0m\r\n');
        this.term.write('\x1b[90mYou can close this tab or refresh to reconnect.\x1b[0m\r\n');
    }
    
    startMonitoring(target, options) {
        this.term.write(`\x1b[33mStarting real-time monitoring of ${target}...\x1b[0m\r\n`);
        this.term.write('\x1b[90m(Press Ctrl+C to stop monitoring)\x1b[0m\r\n\r\n');
        
        // Connect to appropriate stream
        const streamUrl = `${this.apiBaseUrl}/stream/${target}`;
        const eventSource = new EventSource(streamUrl);
        
        eventSource.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                this.displayMonitoringData(target, data);
            } catch (error) {
                this.term.write(`\x1b[31mError parsing monitoring data\x1b[0m\r\n`);
            }
        };
        
        eventSource.onerror = () => {
            this.term.write(`\x1b[31mMonitoring connection lost\x1b[0m\r\n`);
            eventSource.close();
            this.showPrompt();
        };
        
        // Store reference to close later
        this.currentMonitoring = eventSource;
    }
    
    displayMonitoringData(target, data) {
        const timestamp = new Date().toLocaleTimeString();
        
        if (target === 'devices') {
            // Display device status update
            if (data.devices) {
                this.term.write(`\x1b[90m[${timestamp}]\x1b[0m Device status update:\r\n`);
                for (const device of data.devices) {
                    const status = device.status === 'online' ? '\x1b[32m●\x1b[0m' : '\x1b[31m●\x1b[0m';
                    this.term.write(`  ${status} ${device.id}: CPU ${device.cpu}%\r\n`);
                }
                this.term.write('\r\n');
            }
        } else if (target === 'logs') {
            // Display log entry
            const level = data.level || 'INFO';
            const levelColor = {
                'DEBUG': '\x1b[90m',
                'INFO': '\x1b[36m',
                'WARNING': '\x1b[33m',
                'ERROR': '\x1b[31m',
                'CRITICAL': '\x1b[35m'
            }[level] || '\x1b[37m';
            
            this.term.write(`\x1b[90m[${data.timestamp}]\x1b[0m ${levelColor}${level}\x1b[0m: ${data.message}\r\n`);
        }
    }
    
    stopMonitoring() {
        if (this.currentMonitoring) {
            this.currentMonitoring.close();
            this.currentMonitoring = null;
            this.term.write('\r\n\x1b[33mMonitoring stopped\x1b[0m\r\n');
            this.showPrompt();
        }
    }
    
    connectStatusUpdates() {
        // Connect to general status updates
        this.updateConnectionStatus();
        
        // Periodically check connection
        setInterval(() => {
            this.updateConnectionStatus();
        }, 30000);
    }
    
    async updateConnectionStatus() {
        try {
            const response = await fetch(`${this.apiBaseUrl}/health`);
            this.isConnected = response.ok;
        } catch (error) {
            this.isConnected = false;
        }
        
        // Update UI status indicator
        const indicator = document.querySelector('.status-indicator');
        const statusText = document.querySelector('.terminal-status .status-text');
        
        if (indicator && statusText) {
            if (this.isConnected) {
                indicator.className = 'status-indicator online pulse';
                statusText.textContent = 'Connected';
            } else {
                indicator.className = 'status-indicator offline';
                statusText.textContent = 'Disconnected';
            }
        }
    }
    
    // Theme management
    setTheme(themeName) {
        document.body.className = `theme-${themeName}`;
        
        const themes = {
            matrix: {
                background: '#0c0c0c',
                foreground: '#00ff00',
                cursor: '#00ff00'
            },
            amber: {
                background: '#0c0c0c', 
                foreground: '#ffb000',
                cursor: '#ffb000'
            },
            blue: {
                background: '#0c0c0c',
                foreground: '#00aaff',
                cursor: '#00aaff'
            }
        };
        
        if (themes[themeName] && this.term) {
            this.term.setOption('theme', themes[themeName]);
        }
    }
}

// Global terminal instance
let terminal;

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    terminal = new RetireClusterTerminal();
    
    // Setup sidebar toggle
    const sidebarToggle = document.getElementById('sidebarToggle');
    const sidebar = document.querySelector('.terminal-sidebar');
    
    if (sidebarToggle && sidebar) {
        sidebarToggle.addEventListener('click', () => {
            sidebar.classList.toggle('visible');
        });
    }
    
    // Setup theme switcher
    const themeSelect = document.getElementById('themeSelect');
    if (themeSelect) {
        themeSelect.addEventListener('change', (event) => {
            terminal.setTheme(event.target.value);
        });
    }
});

// Export for external use
window.RetireClusterTerminal = RetireClusterTerminal;