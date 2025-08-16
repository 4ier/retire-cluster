"""
Test suite for terminal UI rendering
"""

import unittest
from io import StringIO
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


class TestTerminalRenderer(unittest.TestCase):
    """Test terminal UI rendering functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        from retire_cluster.web.terminal_renderer import TerminalRenderer
        self.renderer = TerminalRenderer()
    
    def test_render_table(self):
        """Test rendering data as ASCII table"""
        data = [
            {"id": "android-001", "status": "online", "cpu": 42, "memory": 2.1, "tasks": 3},
            {"id": "laptop-002", "status": "online", "cpu": 15, "memory": 4.5, "tasks": 1},
            {"id": "raspi-003", "status": "offline", "cpu": 0, "memory": 0, "tasks": 0},
        ]
        
        table = self.renderer.render_table(
            data,
            headers=["ID", "STATUS", "CPU", "MEM", "TASKS"],
            fields=["id", "status", "cpu", "memory", "tasks"]
        )
        
        # Check table structure
        lines = table.split('\n')
        self.assertGreater(len(lines), 3)  # Header + separator + data
        
        # Check header
        self.assertIn("ID", lines[0])
        self.assertIn("STATUS", lines[0])
        self.assertIn("CPU", lines[0])
        
        # Check separator
        self.assertIn("─", lines[1])
        
        # Check data
        self.assertIn("android-001", table)
        self.assertIn("laptop-002", table)
        self.assertIn("raspi-003", table)
    
    def test_render_progress_bar(self):
        """Test rendering progress bar"""
        # Test different percentages
        test_cases = [
            (0, 20, "░"),
            (50, 20, "█"),
            (100, 20, "█"),
        ]
        
        for percentage, width, expected_char in test_cases:
            bar = self.renderer.render_progress_bar(percentage, width)
            
            self.assertEqual(len(bar), width + 2)  # Including [ ]
            self.assertTrue(bar.startswith('['))
            self.assertTrue(bar.endswith(']'))
            
            if percentage > 0:
                self.assertIn(expected_char, bar)
    
    def test_render_status_indicator(self):
        """Test rendering status indicators"""
        test_cases = [
            ("online", "✓"),
            ("offline", "✗"),
            ("warning", "⚠"),
            ("error", "✗"),
            ("unknown", "?"),
        ]
        
        for status, expected in test_cases:
            indicator = self.renderer.render_status_indicator(status)
            self.assertIn(expected, indicator)
    
    def test_render_ascii_chart(self):
        """Test rendering ASCII line chart"""
        data = [10, 20, 30, 25, 35, 40, 30, 20]
        height = 10
        width = 20
        chart = self.renderer.render_ascii_chart(data, width=width, height=height)
        
        lines = chart.split('\n')
        
        # Check dimensions
        self.assertEqual(len(lines), height)
        
        # Check chart contains plotting characters
        chart_chars = set(chart)
        plot_chars = {'╭', '╮', '╯', '╰', '─', '│', '╱', '╲', '█', '▄', '▀'}
        self.assertTrue(any(char in chart_chars for char in plot_chars))
    
    def test_render_metrics_panel(self):
        """Test rendering metrics dashboard panel"""
        metrics = {
            "cpu_usage": 65,
            "memory_usage": 42,
            "disk_usage": 15,
            "network_usage": 85
        }
        
        panel = self.renderer.render_metrics_panel(metrics)
        
        # Check content
        self.assertIn("CPU", panel)
        self.assertIn("65%", panel)
        self.assertIn("MEM", panel)
        self.assertIn("42%", panel)
        
        # Check progress bars
        self.assertIn("[", panel)
        self.assertIn("]", panel)
        self.assertIn("█", panel)  # Should have filled sections
    
    def test_render_device_grid(self):
        """Test rendering device status grid"""
        devices = [
            {"id": "01", "status": "online"},
            {"id": "02", "status": "online"},
            {"id": "03", "status": "offline"},
            {"id": "04", "status": "online"},
            {"id": "05", "status": "warning"},
            {"id": "06", "status": "online"},
        ]
        
        grid = self.renderer.render_device_grid(devices, cols=3)
        
        # Check grid structure
        self.assertIn("┌", grid)  # Top-left corner
        self.assertIn("┐", grid)  # Top-right corner
        self.assertIn("└", grid)  # Bottom-left corner
        self.assertIn("┘", grid)  # Bottom-right corner
        
        # Check device IDs are present
        self.assertIn("01", grid)
        self.assertIn("02", grid)
        self.assertIn("03", grid)
    
    def test_render_log_entries(self):
        """Test rendering log entries"""
        logs = [
            {
                "timestamp": "2024-01-15 10:30:15",
                "level": "INFO",
                "device": "android-001",
                "message": "Device connected"
            },
            {
                "timestamp": "2024-01-15 10:30:16",
                "level": "ERROR",
                "device": "laptop-002",
                "message": "Task failed"
            },
        ]
        
        rendered = self.renderer.render_log_entries(logs)
        
        # Check timestamp format
        self.assertIn("[2024-01-15 10:30:15]", rendered)
        self.assertIn("[2024-01-15 10:30:16]", rendered)
        
        # Check level indicators
        self.assertIn("INFO", rendered)
        self.assertIn("ERROR", rendered)
        
        # Check messages
        self.assertIn("Device connected", rendered)
        self.assertIn("Task failed", rendered)
    
    def test_colorize_output(self):
        """Test output colorization"""
        test_cases = [
            ("online", "green"),
            ("offline", "red"),
            ("warning", "yellow"),
            ("error", "red"),
            ("info", "blue"),
        ]
        
        for text, expected_color in test_cases:
            colored = self.renderer.colorize(text, expected_color)
            
            # When colors are disabled (default for tests), should return original text
            if not self.renderer.colors_enabled:
                self.assertEqual(colored, text)
            else:
                # Should contain ANSI color codes
                self.assertNotEqual(colored, text)
                self.assertIn('\033[', colored)  # ANSI escape sequence
    
    def test_format_bytes(self):
        """Test byte formatting utility"""
        test_cases = [
            (1024, "1.0KB"),
            (1048576, "1.0MB"),
            (1073741824, "1.0GB"),
            (1099511627776, "1.0TB"),
            (512, "512B"),
        ]
        
        for bytes_value, expected in test_cases:
            formatted = self.renderer.format_bytes(bytes_value)
            self.assertEqual(formatted, expected)
    
    def test_format_duration(self):
        """Test duration formatting utility"""
        test_cases = [
            (3661, "1h 1m 1s"),  # 1 hour, 1 minute, 1 second
            (86400, "1d 0h 0m"),  # 1 day
            (3600, "1h 0m 0s"),   # 1 hour
            (60, "1m 0s"),        # 1 minute (our format skips 0h)
            (30, "30s"),          # 30 seconds (our format is simpler)
        ]
        
        for seconds, expected in test_cases:
            formatted = self.renderer.format_duration(seconds)
            self.assertEqual(formatted, expected)
    
    def test_wrap_text(self):
        """Test text wrapping utility"""
        long_text = "This is a very long line of text that should be wrapped at a specific width"
        
        wrapped = self.renderer.wrap_text(long_text, width=20)
        lines = wrapped.split('\n')
        
        # Check that all lines except possibly the last are within width
        for line in lines[:-1]:
            self.assertLessEqual(len(line), 20)
        
        # Check that original text is preserved (accounting for line breaks)
        reconstructed = ' '.join(lines).strip()
        self.assertEqual(reconstructed, long_text)
    
    def test_align_text(self):
        """Test text alignment utility"""
        text = "test"
        width = 10
        
        # Test left alignment
        left_aligned = self.renderer.align_text(text, width, 'left')
        self.assertEqual(left_aligned, "test      ")
        
        # Test right alignment
        right_aligned = self.renderer.align_text(text, width, 'right')
        self.assertEqual(right_aligned, "      test")
        
        # Test center alignment
        center_aligned = self.renderer.align_text(text, width, 'center')
        self.assertEqual(center_aligned, "   test   ")
    
    def test_truncate_text(self):
        """Test text truncation utility"""
        long_text = "This is a very long text"
        
        # Test truncation
        truncated = self.renderer.truncate_text(long_text, 10)
        self.assertEqual(len(truncated), 10)
        self.assertTrue(truncated.endswith("..."))
        
        # Test short text (no truncation)
        short_text = "short"
        not_truncated = self.renderer.truncate_text(short_text, 10)
        self.assertEqual(not_truncated, short_text)


class TestTerminalColors(unittest.TestCase):
    """Test terminal color functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        from retire_cluster.web.terminal_renderer import TerminalColors
        self.colors = TerminalColors()
    
    def test_color_constants(self):
        """Test color constant definitions"""
        # Check that basic colors are defined
        self.assertTrue(hasattr(self.colors, 'RED'))
        self.assertTrue(hasattr(self.colors, 'GREEN'))
        self.assertTrue(hasattr(self.colors, 'YELLOW'))
        self.assertTrue(hasattr(self.colors, 'BLUE'))
        self.assertTrue(hasattr(self.colors, 'CYAN'))
        self.assertTrue(hasattr(self.colors, 'WHITE'))
        self.assertTrue(hasattr(self.colors, 'RESET'))
    
    def test_color_application(self):
        """Test applying colors to text"""
        text = "test"
        
        # Test basic color application
        red_text = self.colors.red(text)
        if self.colors.enabled:
            self.assertIn(self.colors.RED, red_text)
            self.assertIn(self.colors.RESET, red_text)
        else:
            self.assertEqual(red_text, text)
    
    def test_color_combinations(self):
        """Test combining colors and styles"""
        text = "test"
        
        # Test bold
        bold_text = self.colors.bold(text)
        if self.colors.enabled:
            self.assertIn('\033[1m', bold_text)  # Bold ANSI code
        
        # Test underline
        underline_text = self.colors.underline(text)
        if self.colors.enabled:
            self.assertIn('\033[4m', underline_text)  # Underline ANSI code


class TestASCIIArt(unittest.TestCase):
    """Test ASCII art generation"""
    
    def setUp(self):
        """Set up test fixtures"""
        from retire_cluster.web.terminal_renderer import ASCIIArt
        self.ascii_art = ASCIIArt()
    
    def test_logo_generation(self):
        """Test generating ASCII logo"""
        logo = self.ascii_art.generate_logo("RETIRE-CLUSTER")
        
        # Check that logo is generated
        self.assertIsInstance(logo, str)
        self.assertGreater(len(logo), 0)
        
        # Should contain text
        self.assertIn("RETIRE", logo.upper())
    
    def test_banner_generation(self):
        """Test generating banners"""
        banner = self.ascii_art.generate_banner("Welcome to Retire-Cluster")
        
        # Check banner structure
        self.assertIn("─", banner)  # Should have horizontal lines
        self.assertIn("Welcome", banner)
    
    def test_box_drawing(self):
        """Test drawing boxes around text"""
        content = "Test Content"
        box = self.ascii_art.draw_box(content)
        
        # Check box characters
        self.assertIn("┌", box)  # Top-left
        self.assertIn("┐", box)  # Top-right
        self.assertIn("└", box)  # Bottom-left
        self.assertIn("┘", box)  # Bottom-right
        self.assertIn("│", box)  # Vertical
        self.assertIn("─", box)  # Horizontal
        
        # Check content is preserved
        self.assertIn(content, box)


if __name__ == "__main__":
    unittest.main()