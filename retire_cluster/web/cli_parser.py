"""
CLI command parser for Retire-Cluster web interface
"""

import re
import shlex
from typing import Dict, List, Optional, Any


class CommandParser:
    """Parse CLI commands into structured format"""
    
    def __init__(self):
        """Initialize command parser with valid commands"""
        self.valid_verbs = {
            'help', 'clear', 'exit', 'cluster', 'devices', 'device',
            'tasks', 'task', 'monitor', 'export', 'echo', 'grep', 'set'
        }
        
        self.valid_nouns = {
            'cluster': ['status', 'health', 'metrics', 'config'],
            'devices': ['list', 'show', 'ping', 'remove', 'monitor', 'stats'],
            'device': ['show', 'ping', 'remove'],
            'tasks': ['submit', 'list', 'show', 'cancel', 'retry', 'monitor', 'query', 'metrics'],
            'task': ['show', 'cancel', 'retry'],
            'monitor': ['devices', 'tasks', 'logs', 'metrics', 'events', 'alerts'],
            'export': ['devices', 'tasks', 'logs'],
        }
        
        self.short_options = {
            's': 'status',
            'r': 'role',
            'f': 'format',
            'o': 'output',
            'q': 'quiet',
            'v': 'verbose',
            'h': 'help',
            'k': 'api-key',
            'p': 'period',
            'n': 'limit',
        }
    
    def parse(self, command: str) -> Dict[str, Any]:
        """
        Parse a command string into structured format
        
        Args:
            command: Command string to parse
            
        Returns:
            Dictionary with verb, noun, options, and arguments
        """
        if not command or command.isspace():
            return {
                "verb": None,
                "noun": None,
                "options": {},
                "arguments": []
            }
        
        command = command.strip()
        
        # Handle quoted strings properly
        try:
            parts = shlex.split(command)
        except ValueError:
            # Fallback for unclosed quotes
            parts = command.split()
        
        if not parts:
            return {
                "verb": None,
                "noun": None,
                "options": {},
                "arguments": []
            }
        
        verb = parts[0] if parts else None
        noun = None
        options = {}
        arguments = []
        
        i = 1
        
        # For single-word commands like echo, grep - they take arguments not nouns
        if verb in ['echo', 'grep', 'help', 'clear', 'exit']:
            # These commands don't have nouns, rest are arguments
            pass
        elif i < len(parts) and not parts[i].startswith('-'):
            # Check if second part is a noun
            noun = parts[i]
            i += 1
        
        # Parse options and arguments
        while i < len(parts):
            part = parts[i]
            
            if part.startswith('--'):
                # Long option
                if '=' in part:
                    key, value = part[2:].split('=', 1)
                    options[key] = value.strip('\'"')
                else:
                    # Boolean flag
                    options[part[2:]] = True
            elif part.startswith('-') and len(part) > 1:
                # Short option
                if i + 1 < len(parts) and not parts[i + 1].startswith('-'):
                    # Has value
                    key = part[1:]
                    value = parts[i + 1]
                    # Keep short option as is (tests expect this)
                    options[key] = value
                    i += 1
                else:
                    # Boolean flag
                    key = part[1:]
                    options[key] = True
            else:
                # Positional argument
                arguments.append(part)
            
            i += 1
        
        return {
            "verb": verb,
            "noun": noun,
            "options": options,
            "arguments": arguments
        }
    
    def parse_pipeline(self, command: str) -> List[Dict[str, Any]]:
        """
        Parse a pipeline command (commands separated by |)
        
        Args:
            command: Pipeline command string
            
        Returns:
            List of parsed commands
        """
        commands = command.split('|')
        return [self.parse(cmd.strip()) for cmd in commands]
    
    def validate(self, parsed_command: Dict[str, Any]) -> bool:
        """
        Validate a parsed command
        
        Args:
            parsed_command: Parsed command dictionary
            
        Returns:
            True if command is valid, False otherwise
        """
        verb = parsed_command.get('verb')
        noun = parsed_command.get('noun')
        
        if not verb:
            return False
        
        # Check if verb is valid
        if verb not in self.valid_verbs:
            return False
        
        # Some verbs don't need a noun
        if verb in ['help', 'clear', 'exit', 'echo', 'grep', 'set']:
            return True
        
        # Check verb-noun combination
        if verb in self.valid_nouns:
            if not noun:
                return False
            if noun not in self.valid_nouns[verb]:
                return False
        
        return True
    
    def suggest(self, partial: str) -> List[str]:
        """
        Suggest command completions for partial input
        
        Args:
            partial: Partial command string
            
        Returns:
            List of suggested completions
        """
        suggestions = []
        partial = partial.strip().lower()
        
        if not partial:
            return list(self.valid_verbs)
        
        parts = partial.split()
        
        if len(parts) == 1:
            # Suggest verbs
            for verb in self.valid_verbs:
                if verb.startswith(partial):
                    suggestions.append(verb)
        elif len(parts) == 2:
            verb = parts[0]
            partial_noun = parts[1]
            
            # Suggest nouns for the verb
            if verb in self.valid_nouns:
                for noun in self.valid_nouns[verb]:
                    if noun.startswith(partial_noun):
                        suggestions.append(f"{verb} {noun}")
        
        return suggestions
    
    def format_help(self, command: Optional[str] = None) -> str:
        """
        Format help text for commands
        
        Args:
            command: Specific command to get help for
            
        Returns:
            Formatted help text
        """
        if not command:
            # General help
            help_text = "Available commands:\n\n"
            
            for verb in sorted(self.valid_verbs):
                if verb in self.valid_nouns:
                    nouns = ', '.join(self.valid_nouns[verb])
                    help_text += f"  {verb:<10} {nouns}\n"
                else:
                    help_text += f"  {verb}\n"
            
            help_text += "\nUse 'help <command>' for more information"
            return help_text
        
        # Specific command help
        if command in self.valid_verbs:
            if command in self.valid_nouns:
                help_text = f"{command} commands:\n\n"
                for noun in self.valid_nouns[command]:
                    help_text += f"  {command} {noun}\n"
                return help_text
            else:
                return f"{command}: {self._get_command_description(command)}"
        
        return f"Unknown command: {command}"
    
    def _get_command_description(self, command: str) -> str:
        """Get description for a command"""
        descriptions = {
            'help': 'Show help information',
            'clear': 'Clear the screen',
            'exit': 'Exit the interface',
            'echo': 'Echo text to output',
            'grep': 'Filter output with pattern',
            'set': 'Set configuration value',
        }
        return descriptions.get(command, 'No description available')