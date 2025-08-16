"""
Terminal UI renderer for CLI-style output
"""

import re
import math
from typing import List, Dict, Any, Optional, Union
from datetime import datetime


class TerminalColors:
    """ANSI color codes for terminal output"""
    
    def __init__(self, enabled: bool = True):
        """
        Initialize terminal colors
        
        Args:
            enabled: Whether to enable color output
        """
        self.enabled = enabled
        
        if enabled:
            self.RED = '\033[31m'
            self.GREEN = '\033[32m'
            self.YELLOW = '\033[33m'
            self.BLUE = '\033[34m'
            self.MAGENTA = '\033[35m'
            self.CYAN = '\033[36m'
            self.WHITE = '\033[37m'
            self.GRAY = '\033[90m'
            
            # Styles
            self.BOLD = '\033[1m'
            self.DIM = '\033[2m'
            self.UNDERLINE = '\033[4m'
            self.BLINK = '\033[5m'
            self.REVERSE = '\033[7m'
            
            # Reset
            self.RESET = '\033[0m'
        else:
            # Disabled - all empty strings
            attrs = ['RED', 'GREEN', 'YELLOW', 'BLUE', 'MAGENTA', 'CYAN', 'WHITE', 'GRAY',
                    'BOLD', 'DIM', 'UNDERLINE', 'BLINK', 'REVERSE', 'RESET']
            for attr in attrs:
                setattr(self, attr, '')
    
    def colorize(self, text: str, color: str, style: str = '') -> str:
        """Apply color and style to text"""
        if not self.enabled:
            return text
        
        color_map = {
            'red': self.RED,
            'green': self.GREEN,
            'yellow': self.YELLOW,
            'blue': self.BLUE,
            'magenta': self.MAGENTA,
            'cyan': self.CYAN,
            'white': self.WHITE,
            'gray': self.GRAY,
        }
        
        style_map = {
            'bold': self.BOLD,
            'dim': self.DIM,
            'underline': self.UNDERLINE,
            'blink': self.BLINK,
            'reverse': self.REVERSE,
        }
        
        prefix = color_map.get(color, '') + style_map.get(style, '')
        return f"{prefix}{text}{self.RESET}" if prefix else text
    
    def red(self, text: str) -> str:
        return self.colorize(text, 'red')
    
    def green(self, text: str) -> str:
        return self.colorize(text, 'green')
    
    def yellow(self, text: str) -> str:
        return self.colorize(text, 'yellow')
    
    def blue(self, text: str) -> str:
        return self.colorize(text, 'blue')
    
    def cyan(self, text: str) -> str:
        return self.colorize(text, 'cyan')
    
    def gray(self, text: str) -> str:
        return self.colorize(text, 'gray')
    
    def bold(self, text: str) -> str:
        return self.colorize(text, '', 'bold')
    
    def underline(self, text: str) -> str:
        return self.colorize(text, '', 'underline')


class ASCIIArt:
    """ASCII art and box drawing utilities"""
    
    # Box drawing characters
    BOX_CHARS = {
        'horizontal': '─',
        'vertical': '│',
        'top_left': '┌',
        'top_right': '┐',
        'bottom_left': '└',
        'bottom_right': '┘',
        'cross': '┼',
        'tee_up': '┴',
        'tee_down': '┬',
        'tee_left': '┤',
        'tee_right': '├',
    }
    
    def draw_box(self, content: str, padding: int = 1) -> str:
        """
        Draw a box around content
        
        Args:
            content: Text content to box
            padding: Padding inside box
            
        Returns:
            Boxed content string
        """
        lines = content.split('\n')
        max_width = max(len(line) for line in lines) if lines else 0
        
        # Calculate dimensions
        inner_width = max_width + (padding * 2)
        
        # Build box
        result = []
        
        # Top border
        result.append(self.BOX_CHARS['top_left'] + 
                     self.BOX_CHARS['horizontal'] * inner_width + 
                     self.BOX_CHARS['top_right'])
        
        # Padding above content
        for _ in range(padding):
            result.append(self.BOX_CHARS['vertical'] + 
                         ' ' * inner_width + 
                         self.BOX_CHARS['vertical'])
        
        # Content lines
        for line in lines:
            padded_line = ' ' * padding + line.ljust(max_width) + ' ' * padding
            result.append(self.BOX_CHARS['vertical'] + padded_line + self.BOX_CHARS['vertical'])
        
        # Padding below content
        for _ in range(padding):
            result.append(self.BOX_CHARS['vertical'] + 
                         ' ' * inner_width + 
                         self.BOX_CHARS['vertical'])
        
        # Bottom border
        result.append(self.BOX_CHARS['bottom_left'] + 
                     self.BOX_CHARS['horizontal'] * inner_width + 
                     self.BOX_CHARS['bottom_right'])
        
        return '\n'.join(result)
    
    def generate_banner(self, text: str, width: int = 60) -> str:
        """
        Generate a banner with text
        
        Args:
            text: Banner text
            width: Banner width
            
        Returns:
            Banner string
        """
        # Ensure text fits
        if len(text) > width - 4:
            text = text[:width - 7] + "..."
        
        # Center text
        padding = (width - len(text)) // 2
        centered_text = ' ' * padding + text + ' ' * (width - len(text) - padding)
        
        # Build banner
        border = self.BOX_CHARS['horizontal'] * width
        
        return f"{border}\n{centered_text}\n{border}"
    
    def generate_logo(self, text: str) -> str:
        """
        Generate ASCII logo text
        
        Args:
            text: Logo text
            
        Returns:
            ASCII logo
        """
        # Simple ASCII art - could be enhanced with figlet-style fonts
        lines = [
            f"  {text}  ",
            f"{'═' * (len(text) + 4)}",
        ]
        
        return '\n'.join(lines)


class TerminalRenderer:
    """Main terminal rendering class"""
    
    def __init__(self, colors_enabled: bool = False):
        """
        Initialize terminal renderer
        
        Args:
            colors_enabled: Enable color output
        """
        self.colors_enabled = colors_enabled
        self.colors = TerminalColors(colors_enabled)
        self.ascii_art = ASCIIArt()
    
    def render_table(self, data: List[Dict], headers: List[str], 
                    fields: List[str], max_width: Optional[int] = None) -> str:
        """
        Render data as ASCII table
        
        Args:
            data: List of data dictionaries
            headers: Table headers
            fields: Field names corresponding to headers
            max_width: Maximum table width
            
        Returns:
            ASCII table string
        """
        if not data:
            return "No data available"
        
        # Calculate column widths
        col_widths = []
        for i, (header, field) in enumerate(zip(headers, fields)):
            # Width is max of header and data values
            header_width = len(header)
            data_width = max(len(str(row.get(field, ''))) for row in data)
            col_widths.append(max(header_width, data_width))
        
        # Apply max width constraint if specified
        if max_width:
            total_width = sum(col_widths) + len(col_widths) - 1  # Space between columns
            if total_width > max_width:
                # Proportionally reduce column widths
                scale = max_width / total_width
                col_widths = [max(5, int(w * scale)) for w in col_widths]
        
        # Build table
        result = []
        
        # Header row
        header_row = ''
        for i, (header, width) in enumerate(zip(headers, col_widths)):
            if i > 0:
                header_row += ' '
            header_row += header.ljust(width)
        result.append(header_row)
        
        # Separator row
        separator = ''
        for i, width in enumerate(col_widths):
            if i > 0:
                separator += ' '
            separator += '─' * width
        result.append(separator)
        
        # Data rows
        for row in data:
            data_row = ''
            for i, (field, width) in enumerate(zip(fields, col_widths)):
                if i > 0:
                    data_row += ' '
                
                value = str(row.get(field, ''))
                
                # Truncate if too long
                if len(value) > width:
                    value = value[:width-3] + '...'
                
                data_row += value.ljust(width)
            
            result.append(data_row)
        
        return '\n'.join(result)
    
    def render_progress_bar(self, percentage: float, width: int = 20, 
                           filled_char: str = '█', empty_char: str = '░') -> str:
        """
        Render progress bar
        
        Args:
            percentage: Progress percentage (0-100)
            width: Bar width in characters
            filled_char: Character for filled portion
            empty_char: Character for empty portion
            
        Returns:
            Progress bar string
        """
        filled_width = int((percentage / 100) * width)
        empty_width = width - filled_width
        
        bar = '[' + (filled_char * filled_width) + (empty_char * empty_width) + ']'
        return bar
    
    def render_status_indicator(self, status: str) -> str:
        """
        Render status indicator with appropriate symbol and color
        
        Args:
            status: Status string
            
        Returns:
            Colored status indicator
        """
        status_map = {
            'online': ('✓', 'green'),
            'offline': ('✗', 'red'),
            'warning': ('⚠', 'yellow'),
            'error': ('✗', 'red'),
            'pending': ('○', 'yellow'),
            'running': ('●', 'blue'),
            'completed': ('✓', 'green'),
            'failed': ('✗', 'red'),
        }
        
        symbol, color = status_map.get(status.lower(), ('?', 'gray'))
        return self.colors.colorize(symbol, color)
    
    def render_ascii_chart(self, data: List[float], width: int = 40, 
                          height: int = 10, title: str = '') -> str:
        """
        Render ASCII line chart
        
        Args:
            data: Data points to plot
            width: Chart width
            height: Chart height
            title: Chart title
            
        Returns:
            ASCII chart string
        """
        if not data:
            return "No data to display"
        
        # Normalize data to fit height
        min_val = min(data)
        max_val = max(data)
        
        if max_val == min_val:
            # All values are the same
            normalized = [height // 2] * len(data)
        else:
            normalized = [
                int(((val - min_val) / (max_val - min_val)) * (height - 1))
                for val in data
            ]
        
        # Create chart grid
        chart = []
        for y in range(height - 1, -1, -1):  # Top to bottom
            line = ""
            for x in range(min(width, len(data))):
                if x < len(normalized) and normalized[x] == y:
                    line += "█"
                elif x < len(normalized) and normalized[x] > y:
                    line += "│"
                else:
                    line += " "
            chart.append(line)
        
        # Add title if provided
        if title:
            chart.insert(0, title)
            chart.insert(1, "─" * len(title))
        
        return '\n'.join(chart)
    
    def render_metrics_panel(self, metrics: Dict[str, float]) -> str:
        """
        Render metrics dashboard panel
        
        Args:
            metrics: Dictionary of metric name -> percentage
            
        Returns:
            Metrics panel string
        """
        result = []
        
        for name, value in metrics.items():
            # Format metric name
            display_name = name.replace('_', ' ').upper()[:4]
            
            # Render progress bar
            bar = self.render_progress_bar(value, 20)
            
            # Color the percentage based on value
            if value >= 90:
                colored_pct = self.colors.red(f"{value:3.0f}%")
            elif value >= 75:
                colored_pct = self.colors.yellow(f"{value:3.0f}%")
            else:
                colored_pct = self.colors.green(f"{value:3.0f}%")
            
            result.append(f"{display_name} {bar} {colored_pct}")
        
        return '\n'.join(result)
    
    def render_device_grid(self, devices: List[Dict], cols: int = 4) -> str:
        """
        Render device status grid
        
        Args:
            devices: List of device dictionaries
            cols: Number of columns in grid
            
        Returns:
            Device grid string
        """
        if not devices:
            return "No devices"
        
        # Calculate grid dimensions
        rows = math.ceil(len(devices) / cols)
        
        # Build grid
        result = []
        
        # Top border
        top_border = '┌' + '─────┬' * (cols - 1) + '─────┐'
        result.append(top_border)
        
        for row in range(rows):
            # Device row
            device_row = '│'
            for col in range(cols):
                device_idx = row * cols + col
                if device_idx < len(devices):
                    device = devices[device_idx]
                    status_char = self.render_status_indicator(device.get('status', 'unknown'))
                    device_id = device.get('id', '??')[-2:]  # Last 2 chars
                    cell_content = f" {status_char}{device_id} "
                else:
                    cell_content = "     "  # Empty cell
                
                device_row += cell_content
                if col < cols - 1:
                    device_row += '│'
            
            device_row += '│'
            result.append(device_row)
            
            # Row separator (except for last row)
            if row < rows - 1:
                separator = '├' + '─────┼' * (cols - 1) + '─────┤'
                result.append(separator)
        
        # Bottom border
        bottom_border = '└' + '─────┴' * (cols - 1) + '─────┘'
        result.append(bottom_border)
        
        # Add legend
        result.append('')
        result.append('Legend: ✓ Online  ✗ Offline  ⚠ Warning')
        
        return '\n'.join(result)
    
    def render_log_entries(self, logs: List[Dict], max_entries: int = 50) -> str:
        """
        Render log entries
        
        Args:
            logs: List of log dictionaries
            max_entries: Maximum number of entries to show
            
        Returns:
            Formatted log entries
        """
        if not logs:
            return "No log entries"
        
        result = []
        
        # Show most recent entries first
        recent_logs = logs[-max_entries:] if len(logs) > max_entries else logs
        
        for log in recent_logs:
            timestamp = log.get('timestamp', '')
            level = log.get('level', 'INFO')
            device = log.get('device', '')
            message = log.get('message', '')
            
            # Color code log level
            level_colored = self.colors.colorize(level, {
                'DEBUG': 'gray',
                'INFO': 'blue',
                'WARNING': 'yellow',
                'ERROR': 'red',
                'CRITICAL': 'red'
            }.get(level, 'white'))
            
            # Format log line
            device_part = f" {device}" if device else ""
            log_line = f"[{timestamp}] {level_colored}:{device_part} {message}"
            result.append(log_line)
        
        return '\n'.join(result)
    
    def colorize(self, text: str, color: str) -> str:
        """
        Apply color to text
        
        Args:
            text: Text to colorize
            color: Color name
            
        Returns:
            Colorized text
        """
        return self.colors.colorize(text, color)
    
    def format_bytes(self, bytes_value: int) -> str:
        """
        Format bytes in human readable format
        
        Args:
            bytes_value: Number of bytes
            
        Returns:
            Formatted string (e.g., "1.5GB")
        """
        units = ['B', 'KB', 'MB', 'GB', 'TB']
        size = float(bytes_value)
        
        for unit in units:
            if size < 1024.0:
                if unit == 'B':
                    return f"{int(size)}{unit}"  # No decimal for bytes
                else:
                    return f"{size:.1f}{unit}"
            size /= 1024.0
        
        return f"{size:.1f}PB"
    
    def format_duration(self, seconds: int) -> str:
        """
        Format duration in human readable format
        
        Args:
            seconds: Duration in seconds
            
        Returns:
            Formatted string (e.g., "1h 30m 45s")
        """
        days = seconds // 86400
        hours = (seconds % 86400) // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60
        
        if days > 0:
            return f"{days}d {hours}h {minutes}m"
        elif hours > 0:
            return f"{hours}h {minutes}m {secs}s"
        elif minutes > 0:
            return f"{minutes}m {secs}s"
        else:
            return f"{secs}s"
    
    def wrap_text(self, text: str, width: int) -> str:
        """
        Wrap text to specified width
        
        Args:
            text: Text to wrap
            width: Maximum line width
            
        Returns:
            Wrapped text
        """
        import textwrap
        return textwrap.fill(text, width=width)
    
    def align_text(self, text: str, width: int, alignment: str = 'left') -> str:
        """
        Align text within specified width
        
        Args:
            text: Text to align
            width: Target width
            alignment: 'left', 'right', or 'center'
            
        Returns:
            Aligned text
        """
        if alignment == 'left':
            return text.ljust(width)
        elif alignment == 'right':
            return text.rjust(width)
        elif alignment == 'center':
            return text.center(width)
        else:
            return text
    
    def truncate_text(self, text: str, max_length: int, suffix: str = '...') -> str:
        """
        Truncate text if longer than max_length
        
        Args:
            text: Text to truncate
            max_length: Maximum length
            suffix: Suffix to append if truncated
            
        Returns:
            Truncated text
        """
        if len(text) <= max_length:
            return text
        
        return text[:max_length - len(suffix)] + suffix