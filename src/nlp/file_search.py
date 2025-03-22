"""
File Search Module

This module integrates with OpenAI's file search capabilities for directory indexing and search.
It manages vector stores, file uploads, and search operations, and provides specialized search
functions for integration with the multi-step reasoning system.
"""

import os
import json
import tempfile
import requests
import datetime
import re
from io import BytesIO
from typing import Dict, List, Optional, Any, Union, Tuple

from openai import OpenAI
from src.utils.directory_indexer import directory_indexer
from src.core.reasoning import ReasoningStep

class FileSearchManager:
    """
    Manages integration with OpenAI's file search capabilities.
    Handles vector store creation, file uploads, and semantic search.
    Provides specialized search functions for integration with the
    multi-step reasoning system.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the file search manager
        
        Args:
            api_key: OpenAI API key (if None, will use environment variable)
        """
        self.api_key = api_key
        self.client = OpenAI(api_key=self.api_key)
        self.vector_stores = {}
        self.config_path = os.path.expanduser("~/.merlin/file_search_config.json")
        self.ensure_config_directory()
        self.load_config()
    
    def ensure_config_directory(self):
        """Ensure the directory for config file exists"""
        config_dir = os.path.dirname(self.config_path)
        os.makedirs(config_dir, exist_ok=True)
    
    def load_config(self) -> bool:
        """
        Load vector store configuration from file
        
        Returns:
            True if successful, False otherwise
        """
        if not os.path.exists(self.config_path):
            return False
            
        try:
            with open(self.config_path, 'r') as f:
                config = json.load(f)
                
            self.vector_stores = config.get("vector_stores", {})
            return True
        except Exception as e:
            print(f"Error loading file search config: {e}")
            return False
    
    def save_config(self) -> bool:
        """
        Save vector store configuration to file
        
        Returns:
            True if successful, False otherwise
        """
        try:
            config = {
                "vector_stores": self.vector_stores
            }
            
            with open(self.config_path, 'w') as f:
                json.dump(config, f, indent=2)
            return True
        except Exception as e:
            print(f"Error saving file search config: {e}")
            return False
    
    def create_vector_store(self, name: str) -> Dict:
        """
        Create a new vector store
        
        Args:
            name: Name for the vector store
            
        Returns:
            Result information
        """
        try:
            # For testing, we'll create a temporary implementation that doesn't require vector_stores
            # In a production environment, this would use the OpenAI vector_stores API
            
            # Generate a unique ID for this vector store
            import uuid
            vector_store_id = f"vs_{uuid.uuid4().hex[:16]}"
            created_at = datetime.datetime.now().isoformat()
            
            # Save vector store info
            self.vector_stores[name] = {
                "id": vector_store_id,
                "name": name,
                "created_at": created_at,
                "file_counts": 0,
                "directories": []
            }
            
            self.save_config()
            
            print(f"Created test vector store: {name} (ID: {vector_store_id})")
            
            return {
                "success": True,
                "vector_store_id": vector_store_id,
                "name": name
            }
        except Exception as e:
            return {"error": f"Failed to create vector store: {str(e)}"}
    
    def get_vector_stores(self) -> List[Dict]:
        """
        Get list of vector stores
        
        Returns:
            List of vector store information
        """
        try:
            vector_stores = []
            
            for name, store_info in self.vector_stores.items():
                vector_stores.append({
                    "name": name,
                    "id": store_info["id"],
                    "file_count": store_info.get("file_counts", 0),
                    "directories": store_info.get("directories", [])
                })
            
            return vector_stores
        except Exception as e:
            print(f"Error getting vector stores: {e}")
            return []
    
    def create_file(self, file_path: str) -> Dict:
        """
        Create a file in OpenAI's files API
        
        Args:
            file_path: Path to the file to upload
            
        Returns:
            Result information
        """
        try:
            # For testing purposes, we'll create a mock file ID
            # In a production environment, this would actually upload the file to OpenAI
            
            # Generate a unique ID for this file
            import uuid
            file_id = f"file_{uuid.uuid4().hex[:16]}"
            
            filename = os.path.basename(file_path)
            print(f"Created mock file: {filename} (ID: {file_id})")
            
            return {
                "success": True,
                "file_id": file_id,
                "filename": filename
            }
        except Exception as e:
            return {"error": f"Failed to create file: {str(e)}"}
    
    def add_file_to_vector_store(self, vector_store_id: str, file_id: str) -> Dict:
        """
        Add a file to a vector store
        
        Args:
            vector_store_id: ID of the vector store
            file_id: ID of the file to add
            
        Returns:
            Result information
        """
        try:
            # For testing, we'll simulate adding a file to the vector store
            # In a production environment, this would use the OpenAI vector_stores.files.create API
            
            # Update vector store info
            for name, store_info in self.vector_stores.items():
                if store_info["id"] == vector_store_id:
                    store_info["file_counts"] = store_info.get("file_counts", 0) + 1
            
            self.save_config()
            
            print(f"Added file {file_id} to vector store {vector_store_id}")
            
            return {
                "success": True,
                "vector_store_id": vector_store_id,
                "file_id": file_id
            }
        except Exception as e:
            return {"error": f"Failed to add file to vector store: {str(e)}"}
    
    def check_file_status(self, vector_store_id: str) -> Dict:
        """
        Check the status of files in a vector store
        
        Args:
            vector_store_id: ID of the vector store
            
        Returns:
            Status information
        """
        try:
            # For testing, we'll simulate checking file status
            # In a production environment, this would use the OpenAI vector_stores.files.list API
            
            # Find the vector store
            files_status = []
            for name, store_info in self.vector_stores.items():
                if store_info["id"] == vector_store_id:
                    # Simulate file status
                    for i in range(store_info.get("file_counts", 0)):
                        files_status.append({
                            "file_id": f"file_{i}",
                            "object": "vector_store.file",
                            "created_at": datetime.datetime.now().isoformat(),
                            "status": "completed"
                        })
            
            print(f"Checked status of {len(files_status)} files in vector store {vector_store_id}")
            
            return {
                "success": True,
                "vector_store_id": vector_store_id,
                "files": files_status
            }
        except Exception as e:
            return {"error": f"Failed to check file status: {str(e)}"}
    
    def index_directory(self, directory_path: str, vector_store_name: str) -> Dict:
        """
        Index a directory and add it to a vector store
        
        Args:
            directory_path: Path to the directory to index
            vector_store_name: Name of the vector store to use
            
        Returns:
            Result information
        """
        try:
            # Index the directory
            index_result = directory_indexer.index_directory(directory_path)
            
            if "error" in index_result:
                return index_result
            
            # Create or get vector store
            vector_store_id = None
            if vector_store_name in self.vector_stores:
                vector_store_id = self.vector_stores[vector_store_name]["id"]
            else:
                create_result = self.create_vector_store(vector_store_name)
                if "error" in create_result:
                    return create_result
                vector_store_id = create_result["vector_store_id"]
            
            # Generate JSONL file for OpenAI
            temp_dir = tempfile.mkdtemp()
            jsonl_path = os.path.join(temp_dir, "directory_index.jsonl")
            
            jsonl_result = directory_indexer.generate_jsonl_for_directory(
                directory_path,
                jsonl_path
            )
            
            if "error" in jsonl_result:
                return jsonl_result
            
            # Upload JSONL file to OpenAI
            file_result = self.create_file(jsonl_path)
            
            if "error" in file_result:
                return file_result
            
            file_id = file_result["file_id"]
            
            # Add file to vector store
            add_result = self.add_file_to_vector_store(vector_store_id, file_id)
            
            if "error" in add_result:
                return add_result
            
            # Update vector store info
            for name, store_info in self.vector_stores.items():
                if name == vector_store_name:
                    if directory_path not in store_info.get("directories", []):
                        if "directories" not in store_info:
                            store_info["directories"] = []
                        store_info["directories"].append(directory_path)
            
            self.save_config()
            
            # Clean up temp file
            try:
                os.remove(jsonl_path)
                os.rmdir(temp_dir)
            except:
                pass
            
            return {
                "success": True,
                "directory": directory_path,
                "vector_store_name": vector_store_name,
                "vector_store_id": vector_store_id,
                "file_id": file_id,
                "stats": index_result.get("stats", {})
            }
            
        except Exception as e:
            return {"error": f"Failed to index directory: {str(e)}"}
    
    def search(self, query: str, vector_store_name: str, max_results: int = 5) -> Dict:
        """
        Search in a vector store
        
        Args:
            query: Search query
            vector_store_name: Name of the vector store to search in
            max_results: Maximum number of results to return
            
        Returns:
            Search results
        """
        try:
            # Get vector store ID
            if vector_store_name not in self.vector_stores:
                return {"error": f"Vector store not found: {vector_store_name}"}
            
            vector_store_id = self.vector_stores[vector_store_name]["id"]
            
            # For testing, we'll simulate a search response
            # In a production environment, this would use the OpenAI responses.create API with file_search
            
            # Find directories indexed in this vector store
            directories = self.vector_stores[vector_store_name].get("directories", [])
            
            # Generate a simulated response
            print(f"Searching for '{query}' in vector store '{vector_store_name}'")
            print(f"This is a simulated search since vector_stores API is not available")
            print(f"In a real implementation, this would search through {len(directories)} indexed directories")
            
            # In a real implementation, we would get actual search results
            # For now, we'll do a simple substring search in the index
            results = []
            
            # Find directory that was indexed
            if directories:
                directory_path = directories[0]
                dir_index = directory_indexer.get_directory_index(directory_path)
                
                if dir_index and "files" in dir_index:
                    # Do a simple case-insensitive search
                    query_lower = query.lower()
                    
                    print(f"Searching for '{query_lower}' in {len(dir_index['files'])} files")
                    
                    # Search through files
                    for file in dir_index["files"]:
                        file_name = file["name"].lower()
                        # Check if query is in file name (case-insensitive)
                        if query_lower in file_name:
                            print(f"Found match: {file['name']}")
                            results.append({
                                "name": file["name"],
                                "path": file["path"],
                                "category": file["category"],
                                "size": file["size"],
                                "modified": file["modified"]
                            })
                            
                    # If no results found by filename, try searching within directories too
                    if not results:
                        for directory in dir_index["directories"]:
                            if query_lower in directory["path"].lower():
                                # Get files in this matching directory
                                parent_path = directory["path"]
                                for file in dir_index["files"]:
                                    if file["path"].startswith(parent_path):
                                        results.append({
                                            "name": file["name"],
                                            "path": file["path"],
                                            "category": file["category"],
                                            "size": file["size"],
                                            "modified": file["modified"]
                                        })
            
            # Create a mock response object
            # Create a custom result object that can be displayed
            result_text = ""
            if results:
                result_text = f"I found {len(results)} files related to '{query}':\n\n"
                for i, res in enumerate(results[:5], 1):
                    result_text += f"{i}. {res['name']} ({res['category']})\n"
                    result_text += f"   Located at: {res['path']}\n"
                    result_text += f"   Size: {res['size']} bytes, Modified: {res['modified']}\n\n"
            else:
                result_text = f"I couldn't find any files related to '{query}' in your indexed directories.\n"
                result_text += f"The following directories were searched:\n"
                for d in directories:
                    result_text += f"- {d}\n"
            
            # Print the results directly for command-line use
            print(f"\n{result_text}")
            
            # Create a mock response object for API use
            class MockResponse:
                def __init__(self, text):
                    self.text = text
                    # Create a structure similar to what OpenAI API would return
                    self.output = [
                        {
                            "type": "message",
                            "content": [
                                {
                                    "text": text
                                }
                            ]
                        }
                    ]
            
            response = MockResponse(result_text)
            
            return {
                "success": True,
                "response": response,
                "vector_store_name": vector_store_name
            }
            
        except Exception as e:
            return {"error": f"Search failed: {str(e)}"}
    
    def get_indexed_directories(self, vector_store_name: Optional[str] = None) -> List[str]:
        """
        Get list of indexed directories
        
        Args:
            vector_store_name: Optional name of vector store to filter by
            
        Returns:
            List of directory paths
        """
        indexed_dirs = []
        
        if vector_store_name:
            # Get directories for specific vector store
            if vector_store_name in self.vector_stores:
                return self.vector_stores[vector_store_name].get("directories", [])
            return []
        else:
            # Get all indexed directories
            for name, store_info in self.vector_stores.items():
                indexed_dirs.extend(store_info.get("directories", []))
            
            # Remove duplicates
            return list(set(indexed_dirs))
    
    # --- New methods for integration with reasoning system ---
    
    def parse_search_results(self, results: Dict) -> Dict:
        """
        Parse search results into a structured format usable by the reasoning system
        
        Args:
            results: Raw search results
            
        Returns:
            Structured search results with additional metadata
        """
        parsed = {
            "success": False,
            "files": [],
            "summary": {},
            "raw_text": ""
        }
        
        # Check if search was successful
        if "error" in results:
            parsed["error"] = results["error"]
            return parsed
        
        # Extract raw text for context
        if "response" in results and hasattr(results["response"], "text"):
            parsed["raw_text"] = results["response"].text
        
        # Extract file information
        files = []
        text = parsed["raw_text"]
        
        # Parse the text to extract file information
        file_entries = re.findall(r'(\d+)\.\s+([^\n]+)\s+\(([^\)]+)\)\s+Located\s+at:\s+([^\n]+)\s+Size:\s+(\d+)\s+bytes,\s+Modified:\s+([^\n]+)', text)
        
        for entry in file_entries:
            files.append({
                "name": entry[1].strip(),
                "category": entry[2].strip(),
                "path": entry[3].strip(),
                "size": int(entry[4]),
                "modified": entry[5].strip()
            })
        
        parsed["files"] = files
        parsed["success"] = True
        
        # Generate summary statistics
        summary = {
            "total_files": len(files),
            "categories": {},
            "extensions": {},
            "newest_file": None,
            "largest_file": None
        }
        
        if files:
            # Categorize files
            for file in files:
                # Count by category
                category = file["category"]
                if category not in summary["categories"]:
                    summary["categories"][category] = 0
                summary["categories"][category] += 1
                
                # Count by extension
                ext = os.path.splitext(file["name"])[1].lower()
                if ext not in summary["extensions"]:
                    summary["extensions"][ext] = 0
                summary["extensions"][ext] += 1
                
                # Track newest and largest file
                if not summary["newest_file"] or file["modified"] > summary["newest_file"]["modified"]:
                    summary["newest_file"] = file
                
                if not summary["largest_file"] or file["size"] > summary["largest_file"]["size"]:
                    summary["largest_file"] = file
        
        parsed["summary"] = summary
        return parsed
    
    def search_by_type(self, file_type: str, directory: Optional[str] = None, vector_store: str = "default") -> Dict:
        """
        Search for files by type/category
        
        Args:
            file_type: Category of file to search for (e.g., "audio", "document", "image")
            directory: Optional directory to limit search to
            vector_store: Name of vector store to search
            
        Returns:
            Search results
        """
        # Construct query based on file type
        query = f"category:{file_type}"
        if directory:
            query += f" in:{directory}"
        
        # Perform search
        results = self.search(query, vector_store)
        
        # Parse results
        return self.parse_search_results(results)
    
    def search_by_extension(self, extension: str, directory: Optional[str] = None, vector_store: str = "default") -> Dict:
        """
        Search for files with a specific extension
        
        Args:
            extension: File extension (e.g., ".pdf", ".mp3")
            directory: Optional directory to limit search to
            vector_store: Name of vector store to search
            
        Returns:
            Search results
        """
        # Normalize extension
        if not extension.startswith("."):
            extension = f".{extension}"
        
        # Construct query
        query = f"extension:{extension}"
        if directory:
            query += f" in:{directory}"
        
        # Perform search
        results = self.search(query, vector_store)
        
        # Parse results
        return self.parse_search_results(results)
    
    def search_by_name(self, name_pattern: str, directory: Optional[str] = None, vector_store: str = "default") -> Dict:
        """
        Search for files by name pattern
        
        Args:
            name_pattern: Pattern to search for in filenames
            directory: Optional directory to limit search to
            vector_store: Name of vector store to search
            
        Returns:
            Search results
        """
        # Construct query
        query = f"name:{name_pattern}"
        if directory:
            query += f" in:{directory}"
        
        # Perform search
        results = self.search(query, vector_store)
        
        # Parse results
        return self.parse_search_results(results)
    
    def search_by_content(self, content_pattern: str, directory: Optional[str] = None, vector_store: str = "default") -> Dict:
        """
        Search for files by content (semantic search)
        
        Args:
            content_pattern: Content to search for
            directory: Optional directory to limit search to
            vector_store: Name of vector store to search
            
        Returns:
            Search results
        """
        # Construct query
        query = f"content:{content_pattern}"
        if directory:
            query += f" in:{directory}"
        
        # Perform search
        results = self.search(query, vector_store)
        
        # Parse results
        return self.parse_search_results(results)
    
    def get_filtered_files(self, parsed_results: Dict, 
                           filters: Optional[Dict] = None) -> List[Dict]:
        """
        Apply additional filters to parsed search results
        
        Args:
            parsed_results: Parsed search results
            filters: Additional filters to apply
            
        Returns:
            List of files that match the filters
        """
        if not filters:
            return parsed_results["files"]
        
        filtered_files = []
        
        for file in parsed_results["files"]:
            include = True
            
            # Apply each filter
            for key, value in filters.items():
                if key == "min_size" and file.get("size", 0) < value:
                    include = False
                    break
                elif key == "max_size" and file.get("size", 0) > value:
                    include = False
                    break
                elif key == "category" and file.get("category", "") != value:
                    include = False
                    break
                elif key == "extension":
                    file_ext = os.path.splitext(file.get("name", ""))[1].lower()
                    if file_ext != value.lower():
                        include = False
                        break
            
            if include:
                filtered_files.append(file)
        
        return filtered_files
    
    def execute_search_step(self, step: ReasoningStep) -> Dict:
        """
        Execute a search step in the reasoning process
        
        Args:
            step: A reasoning step containing search parameters
            
        Returns:
            Search results formatted for reasoning system
        """
        step_args = step.tool_args
        search_type = step_args.get("search_type", "general")
        
        if search_type == "by_type":
            results = self.search_by_type(
                file_type=step_args.get("file_type", ""),
                directory=step_args.get("directory"),
                vector_store=step_args.get("vector_store", "default")
            )
        elif search_type == "by_extension":
            results = self.search_by_extension(
                extension=step_args.get("extension", ""),
                directory=step_args.get("directory"),
                vector_store=step_args.get("vector_store", "default")
            )
        elif search_type == "by_name":
            results = self.search_by_name(
                name_pattern=step_args.get("name_pattern", ""),
                directory=step_args.get("directory"),
                vector_store=step_args.get("vector_store", "default")
            )
        elif search_type == "by_content":
            results = self.search_by_content(
                content_pattern=step_args.get("content_pattern", ""),
                directory=step_args.get("directory"),
                vector_store=step_args.get("vector_store", "default")
            )
        else:
            # Default to general search
            results = self.search(
                query=step_args.get("query", ""),
                vector_store_name=step_args.get("vector_store", "default"),
                max_results=step_args.get("max_results", 5)
            )
            results = self.parse_search_results(results)
        
        # Apply any additional filters
        filters = step_args.get("filters")
        if filters and results["success"]:
            filtered_files = self.get_filtered_files(results, filters)
            results["filtered_files"] = filtered_files
            results["filtered_count"] = len(filtered_files)
        
        return results

# Initialize global instance
file_search_manager = FileSearchManager()