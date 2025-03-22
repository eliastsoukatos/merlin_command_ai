"""
Context Manager Module

This module manages the context information between reasoning steps,
allowing for state persistence and information sharing across steps
in the multi-step reasoning system.
"""

import os
import json
import time
from typing import Dict, List, Any, Optional, Set, Tuple, Union

from src.utils.directory_manager import directory_manager

class ContextEntry:
    """Represents a single entry in the reasoning context"""
    
    def __init__(self, 
                 key: str, 
                 value: Any, 
                 source: str, 
                 timestamp: Optional[float] = None,
                 metadata: Optional[Dict] = None):
        """
        Initialize a context entry
        
        Args:
            key: Unique identifier for this entry
            value: The value to store
            source: Where this entry came from (e.g., "file_search", "command_execution")
            timestamp: When this entry was created (defaults to current time)
            metadata: Additional information about this entry
        """
        self.key = key
        self.value = value
        self.source = source
        self.timestamp = timestamp or time.time()
        self.metadata = metadata or {}
        self.access_count = 0
        
    def to_dict(self) -> Dict:
        """Convert to dictionary representation"""
        return {
            "key": self.key,
            "value": self.value,
            "source": self.source,
            "timestamp": self.timestamp,
            "metadata": self.metadata,
            "access_count": self.access_count
        }
        
    @classmethod
    def from_dict(cls, data: Dict) -> 'ContextEntry':
        """Create from dictionary representation"""
        entry = cls(
            key=data["key"],
            value=data["value"],
            source=data["source"],
            timestamp=data.get("timestamp"),
            metadata=data.get("metadata", {})
        )
        entry.access_count = data.get("access_count", 0)
        return entry
    
    def access(self) -> None:
        """Mark this entry as accessed"""
        self.access_count += 1


class ReasoningContext:
    """
    Manages context information for multi-step reasoning
    """
    
    def __init__(self, chain_id: str):
        """
        Initialize a reasoning context
        
        Args:
            chain_id: ID of the reasoning chain this context belongs to
        """
        self.chain_id = chain_id
        self.entries: Dict[str, ContextEntry] = {}
        self.initialize_default_context()
    
    def initialize_default_context(self) -> None:
        """Initialize with default context entries"""
        # Add accessible directories
        self.set("approved_directories", 
                 directory_manager.get_all_directories(), 
                 "system", 
                 metadata={"description": "List of directories that are approved for access"})
        
        # Add current working directory
        self.set("current_directory",
                 os.getcwd(),
                 "system",
                 metadata={"description": "Current working directory"})
    
    def set(self, key: str, value: Any, source: str, 
            metadata: Optional[Dict] = None) -> None:
        """
        Set a value in the context
        
        Args:
            key: Key to store the value under
            value: Value to store
            source: Source of the value
            metadata: Additional information about the value
        """
        self.entries[key] = ContextEntry(
            key=key,
            value=value,
            source=source,
            metadata=metadata
        )
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a value from the context
        
        Args:
            key: Key to retrieve
            default: Default value if key not found
            
        Returns:
            The value, or default if not found
        """
        if key in self.entries:
            entry = self.entries[key]
            entry.access()
            return entry.value
        return default
    
    def has(self, key: str) -> bool:
        """
        Check if a key exists in the context
        
        Args:
            key: Key to check
            
        Returns:
            True if the key exists, False otherwise
        """
        return key in self.entries
    
    def update(self, key: str, value: Any, source: Optional[str] = None) -> bool:
        """
        Update an existing context entry
        
        Args:
            key: Key to update
            value: New value
            source: New source (if None, keep existing)
            
        Returns:
            True if updated, False if key not found
        """
        if key not in self.entries:
            return False
        
        entry = self.entries[key]
        entry.value = value
        
        if source is not None:
            entry.source = source
            
        entry.timestamp = time.time()
        return True
    
    def delete(self, key: str) -> bool:
        """
        Delete a context entry
        
        Args:
            key: Key to delete
            
        Returns:
            True if deleted, False if key not found
        """
        if key in self.entries:
            del self.entries[key]
            return True
        return False
    
    def get_all(self) -> Dict[str, Any]:
        """
        Get all context values
        
        Returns:
            Dictionary of all key-value pairs
        """
        return {key: entry.value for key, entry in self.entries.items()}
    
    def get_by_source(self, source: str) -> Dict[str, Any]:
        """
        Get all context values from a specific source
        
        Args:
            source: Source to filter by
            
        Returns:
            Dictionary of key-value pairs from the source
        """
        return {key: entry.value for key, entry in self.entries.items() 
                if entry.source == source}
    
    def to_dict(self) -> Dict:
        """Convert to dictionary representation"""
        return {
            "chain_id": self.chain_id,
            "entries": {key: entry.to_dict() for key, entry in self.entries.items()}
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'ReasoningContext':
        """Create from dictionary representation"""
        context = cls(chain_id=data["chain_id"])
        
        # Replace default entries with the ones from data
        context.entries = {}
        
        for key, entry_data in data.get("entries", {}).items():
            context.entries[key] = ContextEntry.from_dict(entry_data)
            
        return context
    
    def update_from_command_result(self, result: Dict) -> None:
        """
        Update context based on command execution result
        
        Args:
            result: Command execution result
        """
        command = result.get("command", "")
        output = result.get("output", "")
        success = result.get("success", False)
        
        # Store command result
        command_key = f"command_result_{int(time.time())}"
        self.set(command_key, result, "command_execution", 
                 metadata={"command": command, "success": success})
        
        # Store the last command regardless
        self.set("last_command", command, "command_execution")
        self.set("last_command_output", output, "command_execution")
        self.set("last_command_success", success, "command_execution")
        
        # Update command history
        history = self.get("command_history", [])
        history.append(command)
        self.set("command_history", history, "command_execution")
        
        # Try to detect file operations
        if "mkdir" in command:
            # Extract directory from mkdir command
            parts = command.split("mkdir")
            if len(parts) > 1:
                dir_part = parts[1].strip()
                # Remove options
                if dir_part.startswith("-"):
                    dir_part = " ".join(dir_part.split()[1:])
                
                # Store created directory
                self.set("last_created_directory", dir_part, "command_execution")
        
        if "mv" in command or "cp" in command:
            # Track file operations for later use
            self.set("last_file_operation", command, "command_execution")
    
    def update_from_search_result(self, result: Dict) -> None:
        """
        Update context based on file search result
        
        Args:
            result: File search result
        """
        if not result.get("success", False):
            return
            
        files = result.get("files", [])
        
        # Store search results
        search_key = f"search_result_{int(time.time())}"
        self.set(search_key, result, "file_search", 
                 metadata={"file_count": len(files)})
        
        # Always update latest search results
        self.set("last_search_files", files, "file_search")
        self.set("last_search_count", len(files), "file_search")
        
        # Store summary information
        if "summary" in result:
            self.set("last_search_summary", result["summary"], "file_search")
            
            # Extract useful information
            categories = result["summary"].get("categories", {})
            if categories:
                self.set("file_categories", categories, "file_search")
                
            extensions = result["summary"].get("extensions", {})
            if extensions:
                self.set("file_extensions", extensions, "file_search")


class ContextManager:
    """
    Manages reasoning contexts for multiple reasoning chains
    """
    
    def __init__(self):
        """Initialize the context manager"""
        self.contexts: Dict[str, ReasoningContext] = {}
    
    def get_context(self, chain_id: str) -> ReasoningContext:
        """
        Get or create a context for a reasoning chain
        
        Args:
            chain_id: ID of the reasoning chain
            
        Returns:
            The reasoning context
        """
        if chain_id not in self.contexts:
            self.contexts[chain_id] = ReasoningContext(chain_id)
        return self.contexts[chain_id]
    
    def delete_context(self, chain_id: str) -> bool:
        """
        Delete a context
        
        Args:
            chain_id: ID of the reasoning chain
            
        Returns:
            True if deleted, False if not found
        """
        if chain_id in self.contexts:
            del self.contexts[chain_id]
            return True
        return False
    
    def update_context_from_step_result(self, chain_id: str, step_result: Dict, step_info: Dict) -> None:
        """
        Update a context based on a step result
        
        Args:
            chain_id: ID of the reasoning chain
            step_result: Result of the step execution
            step_info: Information about the step
        """
        context = self.get_context(chain_id)
        
        # Update context based on step type
        tool_name = step_info.get("tool_name", "")
        
        if tool_name == "execute_commands":
            context.update_from_command_result(step_result)
        elif tool_name == "search_files":
            context.update_from_search_result(step_result)
        
        # Store the raw step result as well
        step_id = step_info.get("step_id", 0)
        context.set(f"step_result_{step_id}", step_result, "reasoning", 
                  metadata={"step_id": step_id, "tool": tool_name})
    
    def get_step_context(self, chain_id: str, step_id: int) -> Dict:
        """
        Get the relevant context for a specific step
        
        Args:
            chain_id: ID of the reasoning chain
            step_id: ID of the step
            
        Returns:
            Context information relevant to the step
        """
        context = self.get_context(chain_id)
        
        # Get all entries
        full_context = context.get_all()
        
        # Add previous step results specifically
        for i in range(step_id):
            result_key = f"step_result_{i}"
            if context.has(result_key):
                full_context[f"previous_step_{i}_result"] = context.get(result_key)
        
        return full_context

# Initialize global instance
context_manager = ContextManager()