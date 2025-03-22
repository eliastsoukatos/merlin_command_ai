"""
Directory Indexer Module

This module handles the creation and management of directory indexes for the Merlin assistant.
It scans file system directories specified by the user and prepares them for semantic search.
"""

import os
import json
import time
import datetime
import hashlib
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Any

class DirectoryIndexer:
    """Class to manage directory indexing for Merlin assistant"""
    
    def __init__(self, config=None):
        """Initialize the directory indexer"""
        self.config = config or {}
        self.indexed_directories = {}
        self.index_path = os.path.expanduser("~/.merlin/directory_index.json")
        self.ensure_index_directory()
        self.load_index()
    
    def ensure_index_directory(self):
        """Ensure the directory for the index file exists"""
        index_dir = os.path.dirname(self.index_path)
        os.makedirs(index_dir, exist_ok=True)
    
    def index_directory(self, directory_path: str, max_depth: int = 3) -> Dict:
        """
        Index a specific directory and its contents
        
        Args:
            directory_path: Path to the directory to index
            max_depth: Maximum depth to traverse
            
        Returns:
            Directory index information
        """
        if not os.path.isdir(directory_path):
            return {"error": f"Directory not found: {directory_path}"}
        
        # Get absolute path
        directory_path = os.path.abspath(directory_path)
        
        start_time = time.time()
        
        # Create index data structure
        index_data = {
            "path": directory_path,
            "last_indexed": datetime.datetime.now().isoformat(),
            "files": [],
            "directories": []
        }
        
        # Track statistics
        stats = {
            "total_files": 0,
            "total_dirs": 0,
            "skipped_files": 0,
            "indexed_files": 0,
            "total_size": 0
        }
        
        # Walk the directory
        for root, dirs, files in os.walk(directory_path):
            # Calculate current depth
            relative_path = os.path.relpath(root, directory_path)
            current_depth = 0 if relative_path == '.' else relative_path.count(os.sep) + 1
            
            # Skip if beyond max depth
            if current_depth > max_depth:
                continue
            
            # Add current directory to index
            rel_dir_path = os.path.relpath(root, directory_path)
            dir_info = {
                "path": root,
                "relative_path": rel_dir_path if rel_dir_path != '.' else '',
                "name": os.path.basename(root),
                "depth": current_depth
            }
            index_data["directories"].append(dir_info)
            stats["total_dirs"] += 1
            
            # Skip hidden directories for future traversal
            dirs[:] = [d for d in dirs if not d.startswith('.')]
            
            # Process files in current directory
            for filename in files:
                # Skip hidden files
                if filename.startswith('.'):
                    stats["skipped_files"] += 1
                    continue
                
                file_path = os.path.join(root, filename)
                
                try:
                    # Get file stats
                    file_stat = os.stat(file_path)
                    file_size = file_stat.st_size
                    stats["total_size"] += file_size
                    stats["total_files"] += 1
                    
                    # Check if file is too large (>10MB)
                    if file_size > 10 * 1024 * 1024:
                        stats["skipped_files"] += 1
                        continue
                    
                    # Create file info
                    file_info = {
                        "path": file_path,
                        "relative_path": os.path.relpath(file_path, directory_path),
                        "name": filename,
                        "extension": os.path.splitext(filename)[1].lower(),
                        "size": file_size,
                        "modified": datetime.datetime.fromtimestamp(file_stat.st_mtime).isoformat(),
                        "created": datetime.datetime.fromtimestamp(file_stat.st_ctime).isoformat(),
                        "category": self._categorize_file(filename)
                    }
                    
                    # Add to index
                    index_data["files"].append(file_info)
                    stats["indexed_files"] += 1
                    
                except (PermissionError, OSError, FileNotFoundError) as e:
                    stats["skipped_files"] += 1
                    continue
        
        # Add statistics to index
        index_data["stats"] = stats
        index_data["elapsed_time"] = time.time() - start_time
        
        # Update the indexed directories
        self.indexed_directories[directory_path] = index_data
        
        # Save the updated index
        self.save_index()
        
        return index_data
    
    def save_index(self) -> bool:
        """
        Save the index to a JSON file
        
        Returns:
            True if successful, False otherwise
        """
        if not self.indexed_directories:
            return False
            
        try:
            index_data = {
                "indexed_directories": self.indexed_directories,
                "last_saved": datetime.datetime.now().isoformat()
            }
            
            with open(self.index_path, 'w') as f:
                json.dump(index_data, f, indent=2)
            return True
        except Exception as e:
            print(f"Error saving index: {e}")
            return False
    
    def load_index(self) -> bool:
        """
        Load the index from a JSON file
        
        Returns:
            True if successful, False otherwise
        """
        if not os.path.exists(self.index_path):
            return False
            
        try:
            with open(self.index_path, 'r') as f:
                index_data = json.load(f)
                
            self.indexed_directories = index_data.get("indexed_directories", {})
            return True
        except Exception as e:
            print(f"Error loading index: {e}")
            return False
    
    def get_indexed_directories(self) -> List[str]:
        """
        Get a list of indexed directories
        
        Returns:
            List of directory paths
        """
        return list(self.indexed_directories.keys())
    
    def get_directory_index(self, directory_path: str) -> Optional[Dict]:
        """
        Get the index for a specific directory
        
        Args:
            directory_path: Path to the directory
            
        Returns:
            Directory index or None if not found
        """
        directory_path = os.path.abspath(directory_path)
        return self.indexed_directories.get(directory_path)
    
    def remove_directory_index(self, directory_path: str) -> bool:
        """
        Remove a directory from the index
        
        Args:
            directory_path: Path to the directory
            
        Returns:
            True if removed, False if not found
        """
        directory_path = os.path.abspath(directory_path)
        if directory_path in self.indexed_directories:
            del self.indexed_directories[directory_path]
            self.save_index()
            return True
        return False
    
    def get_index_summary(self) -> Dict:
        """Get a summary of the current index"""
        if not self.indexed_directories:
            return {"status": "No indexed directories"}
        
        total_dirs = 0
        total_files = 0
        total_size = 0
        
        for dir_path, dir_data in self.indexed_directories.items():
            total_dirs += dir_data.get("stats", {}).get("total_dirs", 0)
            total_files += dir_data.get("stats", {}).get("indexed_files", 0)
            total_size += dir_data.get("stats", {}).get("total_size", 0)
        
        return {
            "indexed_directories": len(self.indexed_directories),
            "total_directories": total_dirs,
            "total_files": total_files,
            "total_size_bytes": total_size,
            "total_size_mb": total_size / (1024 * 1024)
        }
    
    def clear_index(self) -> bool:
        """
        Clear the entire index
        
        Returns:
            True if successful
        """
        self.indexed_directories = {}
        return self.save_index()
    
    def _categorize_file(self, filename: str) -> str:
        """Categorize a file based on its extension"""
        extension = os.path.splitext(filename)[1].lower()
        
        # Document files
        if extension in ['.txt', '.pdf', '.doc', '.docx', '.odt', '.rtf', '.md', '.tex']:
            return "document"
            
        # Image files
        if extension in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp', '.svg']:
            return "image"
            
        # Audio files
        if extension in ['.mp3', '.wav', '.flac', '.ogg', '.aac', '.m4a']:
            return "audio"
            
        # Video files
        if extension in ['.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm']:
            return "video"
            
        # Code files
        if extension in ['.py', '.js', '.html', '.css', '.java', '.cpp', '.c', '.h', '.sh', '.rb']:
            return "code"
            
        # Data files
        if extension in ['.csv', '.json', '.xml', '.yaml', '.yml', '.sql', '.db']:
            return "data"
            
        # Archive files
        if extension in ['.zip', '.rar', '.tar', '.gz', '.7z']:
            return "archive"
            
        # Executable files
        if extension in ['.exe', '.app', '.deb', '.rpm', '.dmg', '.apk']:
            return "executable"
            
        # Presentation files
        if extension in ['.ppt', '.pptx', '.odp', '.key']:
            return "presentation"
            
        # Spreadsheet files
        if extension in ['.xls', '.xlsx', '.ods', '.csv']:
            return "spreadsheet"
            
        return "other"
    
    def generate_jsonl_for_directory(self, directory_path: str, output_path: str) -> Dict:
        """
        Generate a JSONL file for a directory index suitable for OpenAI upload
        
        Args:
            directory_path: Path to the indexed directory
            output_path: Path to save the JSONL file
            
        Returns:
            Result information
        """
        directory_path = os.path.abspath(directory_path)
        directory_index = self.get_directory_index(directory_path)
        
        if not directory_index:
            return {"error": f"Directory not indexed: {directory_path}"}
        
        try:
            # Create chunks for the directory structure
            chunks = self._create_directory_chunks(directory_index)
            
            # Write chunks to JSONL file
            with open(output_path, 'w') as f:
                for i, chunk in enumerate(chunks):
                    # Each line is a JSON object
                    line = {
                        "id": f"chunk_{i}",
                        "text": chunk["text"],
                        "metadata": {
                            "source": chunk["source"],
                            "type": chunk["type"],
                            "path": chunk["path"]
                        }
                    }
                    f.write(json.dumps(line) + '\n')
            
            return {
                "success": True,
                "chunks_count": len(chunks),
                "output_path": output_path
            }
                
        except Exception as e:
            return {"error": f"Failed to generate JSONL: {str(e)}"}
    
    def _create_directory_chunks(self, directory_index: Dict) -> List[Dict]:
        """
        Create text chunks from a directory index
        
        Args:
            directory_index: Directory index data
            
        Returns:
            List of chunks
        """
        chunks = []
        
        # Root directory chunk
        root_path = directory_index["path"]
        root_chunk = {
            "text": f"Directory: {root_path}\n"
                   f"Last indexed: {directory_index['last_indexed']}\n"
                   f"Total files: {directory_index['stats']['indexed_files']}\n"
                   f"Total directories: {directory_index['stats']['total_dirs']}\n\n"
                   f"This is the root directory that contains all indexed files and subdirectories.",
            "source": "directory_structure",
            "type": "directory",
            "path": root_path
        }
        chunks.append(root_chunk)
        
        # Directory chunks
        for directory in directory_index["directories"]:
            # Skip root directory (already added)
            if directory["path"] == root_path:
                continue
                
            dir_chunk = {
                "text": f"Directory: {directory['path']}\n"
                       f"Name: {directory['name']}\n"
                       f"Relative path: {directory['relative_path']}\n"
                       f"Depth: {directory['depth']}\n\n"
                       f"This is a subdirectory within {root_path}.",
                "source": "directory_structure",
                "type": "directory",
                "path": directory["path"]
            }
            chunks.append(dir_chunk)
        
        # Create file chunks by grouping similar files
        file_groups = self._group_similar_files(directory_index["files"])
        
        for group_name, files in file_groups.items():
            # Skip empty groups
            if not files:
                continue
                
            # Create a chunk for each group with up to 10 files
            for i in range(0, len(files), 10):
                group_files = files[i:i+10]
                
                file_list_text = "\n".join([
                    f"- {file['name']} ({file['size']} bytes, modified: {file['modified']})"
                    for file in group_files
                ])
                
                file_paths_text = "\n".join([
                    f"- {file['path']}"
                    for file in group_files
                ])
                
                group_chunk = {
                    "text": f"File Group: {group_name} (Part {i//10 + 1})\n\n"
                           f"Files in this group:\n{file_list_text}\n\n"
                           f"Full paths:\n{file_paths_text}\n\n"
                           f"These files are {group_name} files located in or under {root_path}.",
                    "source": "file_group",
                    "type": group_name,
                    "path": root_path
                }
                chunks.append(group_chunk)
        
        return chunks
    
    def _group_similar_files(self, files: List[Dict]) -> Dict[str, List[Dict]]:
        """
        Group similar files together
        
        Args:
            files: List of file information
            
        Returns:
            Dictionary of file groups
        """
        groups = {}
        
        # Group by category
        for file in files:
            category = file["category"]
            if category not in groups:
                groups[category] = []
            groups[category].append(file)
        
        return groups

# Initialize global instance
directory_indexer = DirectoryIndexer()