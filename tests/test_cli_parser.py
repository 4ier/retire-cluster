"""
Test suite for CLI command parser
"""

import unittest
from typing import Dict, List, Optional
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


class TestCommandParser(unittest.TestCase):
    """Test CLI command parsing functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        from retire_cluster.web.cli_parser import CommandParser
        self.parser = CommandParser()
    
    def test_parse_simple_command(self):
        """Test parsing simple commands without arguments"""
        # Test cases: command -> expected result
        test_cases = [
            ("help", {"verb": "help", "noun": None, "options": {}, "arguments": []}),
            ("clear", {"verb": "clear", "noun": None, "options": {}, "arguments": []}),
            ("exit", {"verb": "exit", "noun": None, "options": {}, "arguments": []}),
        ]
        
        for command, expected in test_cases:
            with self.subTest(command=command):
                result = self.parser.parse(command)
                self.assertEqual(result, expected)
    
    def test_parse_verb_noun_commands(self):
        """Test parsing commands with verb and noun"""
        test_cases = [
            ("cluster status", 
             {"verb": "cluster", "noun": "status", "options": {}, "arguments": []}),
            ("devices list",
             {"verb": "devices", "noun": "list", "options": {}, "arguments": []}),
            ("tasks submit",
             {"verb": "tasks", "noun": "submit", "options": {}, "arguments": []}),
        ]
        
        for command, expected in test_cases:
            with self.subTest(command=command):
                result = self.parser.parse(command)
                self.assertEqual(result, expected)
    
    def test_parse_commands_with_options(self):
        """Test parsing commands with options"""
        test_cases = [
            ("devices list --status=online",
             {"verb": "devices", "noun": "list", 
              "options": {"status": "online"}, "arguments": []}),
            ("devices list --status=online --role=worker",
             {"verb": "devices", "noun": "list",
              "options": {"status": "online", "role": "worker"}, "arguments": []}),
            ("tasks list --format=json --limit=10",
             {"verb": "tasks", "noun": "list",
              "options": {"format": "json", "limit": "10"}, "arguments": []}),
        ]
        
        for command, expected in test_cases:
            with self.subTest(command=command):
                result = self.parser.parse(command)
                self.assertEqual(result, expected)
    
    def test_parse_commands_with_arguments(self):
        """Test parsing commands with positional arguments"""
        test_cases = [
            ("devices show android-001",
             {"verb": "devices", "noun": "show",
              "options": {}, "arguments": ["android-001"]}),
            ("devices ping android-001 laptop-002",
             {"verb": "devices", "noun": "ping",
              "options": {}, "arguments": ["android-001", "laptop-002"]}),
            ("tasks cancel task-abc123",
             {"verb": "tasks", "noun": "cancel",
              "options": {}, "arguments": ["task-abc123"]}),
        ]
        
        for command, expected in test_cases:
            with self.subTest(command=command):
                result = self.parser.parse(command)
                self.assertEqual(result, expected)
    
    def test_parse_complex_commands(self):
        """Test parsing complex commands with options and arguments"""
        test_cases = [
            ('tasks submit echo --payload=\'{"message":"test"}\' --priority=high',
             {"verb": "tasks", "noun": "submit",
              "options": {"payload": '{"message":"test"}', "priority": "high"},
              "arguments": ["echo"]}),
            ("monitor logs --device=android-001 --level=error --tail=100",
             {"verb": "monitor", "noun": "logs",
              "options": {"device": "android-001", "level": "error", "tail": "100"},
              "arguments": []}),
        ]
        
        for command, expected in test_cases:
            with self.subTest(command=command):
                result = self.parser.parse(command)
                self.assertEqual(result, expected)
    
    def test_parse_short_options(self):
        """Test parsing short option forms"""
        test_cases = [
            ("devices list -s online -r worker",
             {"verb": "devices", "noun": "list",
              "options": {"s": "online", "r": "worker"}, "arguments": []}),
            ("export devices -f csv -o devices.csv",
             {"verb": "export", "noun": "devices",
              "options": {"f": "csv", "o": "devices.csv"}, "arguments": []}),
        ]
        
        for command, expected in test_cases:
            with self.subTest(command=command):
                result = self.parser.parse(command)
                self.assertEqual(result, expected)
    
    def test_validate_command(self):
        """Test command validation"""
        # Valid commands should return True
        valid_commands = [
            "cluster status",
            "devices list",
            "tasks submit echo --payload='{}'",
            "monitor logs",
        ]
        
        for command in valid_commands:
            with self.subTest(command=command):
                parsed = self.parser.parse(command)
                self.assertTrue(self.parser.validate(parsed))
        
        # Invalid commands should return False
        invalid_commands = [
            "invalid command",
            "cluster invalid_action",
            "devices",  # Missing noun
        ]
        
        for command in invalid_commands:
            with self.subTest(command=command):
                parsed = self.parser.parse(command)
                self.assertFalse(self.parser.validate(parsed))
    
    def test_parse_quoted_strings(self):
        """Test parsing commands with quoted strings"""
        test_cases = [
            ('echo "hello world"',
             {"verb": "echo", "noun": None,
              "options": {}, "arguments": ["hello world"]}),
            ("tasks submit 'complex task' --name='my task'",
             {"verb": "tasks", "noun": "submit",
              "options": {"name": "my task"}, "arguments": ["complex task"]}),
        ]
        
        for command, expected in test_cases:
            with self.subTest(command=command):
                result = self.parser.parse(command)
                self.assertEqual(result, expected)
    
    def test_parse_pipe_commands(self):
        """Test parsing commands with pipes"""
        command = "devices list | grep online"
        result = self.parser.parse_pipeline(command)
        
        expected = [
            {"verb": "devices", "noun": "list", "options": {}, "arguments": []},
            {"verb": "grep", "noun": None, "options": {}, "arguments": ["online"]},
        ]
        
        self.assertEqual(result, expected)
    
    def test_command_suggestions(self):
        """Test command auto-completion suggestions"""
        test_cases = [
            ("dev", ["devices"]),
            ("devices l", ["devices list"]),
            ("cluster s", ["cluster status"]),
            ("task", ["tasks"]),
        ]
        
        for partial, expected_suggestions in test_cases:
            with self.subTest(partial=partial):
                suggestions = self.parser.suggest(partial)
                for expected in expected_suggestions:
                    self.assertIn(expected, suggestions)
    
    def test_parse_empty_or_whitespace(self):
        """Test parsing empty or whitespace-only commands"""
        test_cases = [
            ("", {"verb": None, "noun": None, "options": {}, "arguments": []}),
            ("   ", {"verb": None, "noun": None, "options": {}, "arguments": []}),
            ("\t\n", {"verb": None, "noun": None, "options": {}, "arguments": []}),
        ]
        
        for command, expected in test_cases:
            with self.subTest(command=repr(command)):
                result = self.parser.parse(command)
                self.assertEqual(result, expected)
    
    def test_parse_special_characters(self):
        """Test handling special characters in commands"""
        test_cases = [
            ("devices show device-001",  # Hyphen in argument
             {"verb": "devices", "noun": "show",
              "options": {}, "arguments": ["device-001"]}),
            ("tasks submit --payload='{\"key\":\"value\"}'",  # JSON in option
             {"verb": "tasks", "noun": "submit",
              "options": {"payload": '{"key":"value"}'}, "arguments": []}),
        ]
        
        for command, expected in test_cases:
            with self.subTest(command=command):
                result = self.parser.parse(command)
                self.assertEqual(result, expected)


class TestCommandExecutor(unittest.TestCase):
    """Test command execution functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        from retire_cluster.web.cli_executor import CommandExecutor
        from unittest.mock import Mock
        
        # Create mock cluster server
        self.mock_cluster = Mock()
        self.mock_cluster.get_devices.return_value = [
            {"id": "android-001", "status": "online", "cpu": 42, "memory": 2.1},
            {"id": "laptop-002", "status": "online", "cpu": 15, "memory": 4.5},
            {"id": "raspi-003", "status": "offline", "cpu": 0, "memory": 0},
        ]
        
        self.executor = CommandExecutor(self.mock_cluster)
    
    def test_execute_help_command(self):
        """Test executing help command"""
        result = self.executor.execute({"verb": "help", "noun": None, 
                                       "options": {}, "arguments": []})
        
        self.assertEqual(result["status"], "success")
        self.assertIn("output", result)
        self.assertIn("Available commands", result["output"])
    
    def test_execute_devices_list(self):
        """Test executing devices list command"""
        result = self.executor.execute({"verb": "devices", "noun": "list",
                                       "options": {}, "arguments": []})
        
        self.assertEqual(result["status"], "success")
        self.assertIn("android-001", result["output"])
        self.assertIn("laptop-002", result["output"])
        self.assertIn("raspi-003", result["output"])
    
    def test_execute_devices_list_with_filter(self):
        """Test executing devices list with status filter"""
        result = self.executor.execute({"verb": "devices", "noun": "list",
                                       "options": {"status": "online"}, 
                                       "arguments": []})
        
        self.assertEqual(result["status"], "success")
        self.assertIn("android-001", result["output"])
        self.assertIn("laptop-002", result["output"])
        self.assertNotIn("raspi-003", result["output"])
    
    def test_execute_invalid_command(self):
        """Test executing invalid command"""
        result = self.executor.execute({"verb": "invalid", "noun": "command",
                                       "options": {}, "arguments": []})
        
        self.assertEqual(result["status"], "error")
        self.assertIn("error", result)
        self.assertIn("Unknown command", result["error"])
    
    def test_execute_with_format_option(self):
        """Test executing command with format option"""
        test_cases = ["json", "csv", "tsv", "text"]
        
        for format_type in test_cases:
            with self.subTest(format=format_type):
                result = self.executor.execute({
                    "verb": "devices", "noun": "list",
                    "options": {"format": format_type},
                    "arguments": []
                })
                
                self.assertEqual(result["status"], "success")
                self.assertEqual(result["format"], format_type)


if __name__ == "__main__":
    unittest.main()