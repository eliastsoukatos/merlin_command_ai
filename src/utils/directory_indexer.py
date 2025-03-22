"""
Directory Indexer Module

This module handles the creation and management of directory indexes for the Merlin assistant.
It scans the file system and creates a structured representation of the directories and files.
"""

import os
import json
import time
from pathlib import Path
from typing import Dict, List, Optional

class DirectoryIndexer:
    """Class to manage directory indexing for Merlin assistant"""
    
    def __init__(self, config=None):
        """Initialize the directory indexer"""
        self.config = config or {}
        self.root_dirs = self._get_default_directories()
        self.index_data = {}
        self.last_indexed = None
    
    def _get_default_directories(self) -> List[str]:
        """Get default directories to index"""
        home_dir = str(Path.home())
        return [
            home_dir,
            os.path.join(home_dir, "Desktop"),
            os.path.join(home_dir, "Documents"),
            os.path.join(home_dir, "Downloads"),
            os.path.join(home_dir, "Pictures"),
            os.path.join(home_dir, "Music"),
            os.path.join(home_dir, "Videos")
        ]
    
    def add_directory(self, directory_path: str):
        """Add a new directory to the index"""
        if os.path.isdir(directory_path):
            directory_path = os.path.abspath(directory_path)
            if directory_path not in self.root_dirs:
                self.root_dirs.append(directory_path)
                return True
        return False
    
    def build_index(self, max_depth: int = 3, file_extensions: Optional[List[str]] = None) -> Dict:
        """
        Build an index of directories and files
        
        Args:
            max_depth: Maximum depth to index
            file_extensions: Optional list of file extensions to include (e.g., ['.txt', '.pdf'])
            
        Returns:
            Dictionary with the directory index
        """
        start_time = time.time()
        index = {
            "directories": {},
            "metadata": {
                "indexed_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                "root_directories": self.root_dirs,
                "max_depth": max_depth
            }
        }
        
        for root_dir in self.root_dirs:
            if os.path.isdir(root_dir):
                index["directories"][root_dir] = self._index_directory(
                    root_dir, 
                    max_depth=max_depth,
                    current_depth=0,
                    file_extensions=file_extensions
                )
        
        index["metadata"]["elapsed_time"] = time.time() - start_time
        self.index_data = index
        self.last_indexed = time.time()
        
        return index
    
    def _index_directory(
        self, 
        directory: str, 
        max_depth: int = 3, 
        current_depth: int = 0,
        file_extensions: Optional[List[str]] = None
    ) -> Dict:
        """
        Recursively index a directory
        
        Args:
            directory: Directory path to index
            max_depth: Maximum depth to traverse
            current_depth: Current depth in the traversal
            file_extensions: Optional list of file extensions to include
            
        Returns:
            Dictionary with directory structure
        """
        if current_depth > max_depth:
            return {"summary": f"Max depth reached ({max_depth})"}
        
        result = {
            "path": directory,
            "name": os.path.basename(directory),
            "subdirectories": {},
            "files": []
        }
        
        try:
            entries = list(os.scandir(directory))
            
            # Add subdirectories
            subdirs = [entry for entry in entries if entry.is_dir()]
            for subdir in subdirs:
                # Skip hidden directories
                if subdir.name.startswith('.'):
                    continue
                    
                subdir_path = os.path.join(directory, subdir.name)
                result["subdirectories"][subdir.name] = self._index_directory(
                    subdir_path, 
                    max_depth=max_depth,
                    current_depth=current_depth + 1,
                    file_extensions=file_extensions
                )
            
            # Add files
            files = [entry for entry in entries if entry.is_file()]
            for file_entry in files:
                # Skip hidden files
                if file_entry.name.startswith('.'):
                    continue
                    
                # Check file extension if filter is provided
                if file_extensions:
                    ext = os.path.splitext(file_entry.name)[1].lower()
                    if ext not in file_extensions:
                        continue
                
                stat = file_entry.stat()
                result["files"].append({
                    "name": file_entry.name,
                    "path": os.path.join(directory, file_entry.name),
                    "size": stat.st_size,
                    "modified": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(stat.st_mtime)),
                    "extension": os.path.splitext(file_entry.name)[1].lower()
                })
            
        except (PermissionError, OSError) as e:
            result["error"] = str(e)
        
        return result
    
    def save_index(self, output_path: str) -> bool:
        """
        Save the index to a JSON file
        
        Args:
            output_path: Path to save the index
            
        Returns:
            True if successful, False otherwise
        """
        if not self.index_data:
            return False
            
        try:
            with open(output_path, 'w') as f:
                json.dump(self.index_data, f, indent=2)
            return True
        except Exception as e:
            print(f"Error saving index: {e}")
            return False
    
    def load_index(self, input_path: str) -> bool:
        """
        Load an index from a JSON file
        
        Args:
            input_path: Path to load the index from
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with open(input_path, 'r') as f:
                self.index_data = json.load(f)
            self.last_indexed = os.path.getmtime(input_path)
            return True
        except Exception as e:
            print(f"Error loading index: {e}")
            return False
    
    def get_index_summary(self) -> Dict:
        """Get a summary of the current index"""
        if not self.index_data:
            return {"status": "No index available"}
        
        total_dirs = 0
        total_files = 0
        root_dirs = list(self.index_data.get("directories", {}).keys())
        
        # Count directories and files
        for root_dir, content in self.index_data.get("directories", {}).items():
            total_dirs += self._count_dirs(content)
            total_files += self._count_files(content)
        
        return {
            "indexed_at": self.index_data.get("metadata", {}).get("indexed_at", "Unknown"),
            "root_directories": root_dirs,
            "total_directories": total_dirs,
            "total_files": total_files
        }
    
    def _count_dirs(self, dir_data: Dict) -> int:
        """Count the number of directories in the index"""
        count = 1  # Count this directory
        for subdir_name, subdir_data in dir_data.get("subdirectories", {}).items():
            count += self._count_dirs(subdir_data)
        return count
    
    def _count_files(self, dir_data: Dict) -> int:
        """Count the number of files in the index"""
        count = len(dir_data.get("files", []))
        for subdir_name, subdir_data in dir_data.get("subdirectories", {}).items():
            count += self._count_files(subdir_data)
        return count

# Initialize a global instance
directory_indexer = DirectoryIndexer()