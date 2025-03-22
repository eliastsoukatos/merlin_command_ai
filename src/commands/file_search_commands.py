"""
File Search Commands Module

This module provides command-line interface for file search operations.
"""

import os
import json
import argparse
from typing import Dict, List, Optional

from src.utils.directory_indexer import directory_indexer
from src.nlp.file_search import file_search_manager

class FileSearchCommands:
    """
    Provides command-line commands for file search operations
    """
    
    @staticmethod
    def index(args) -> Dict:
        """
        Index a directory
        
        Args:
            args: Command arguments with directory and vector_store parameters
            
        Returns:
            Result information
        """
        directory = args.directory
        vector_store = args.vector_store or "default"
        max_depth = args.max_depth
        
        if not directory:
            return {"error": "Directory path is required"}
        
        if not os.path.isdir(directory):
            return {"error": f"Directory not found: {directory}"}
        
        result = file_search_manager.index_directory(directory, vector_store)
        
        if "success" in result and result["success"]:
            print(f"\nSuccessfully indexed directory: {directory}")
            print(f"Added to vector store: {vector_store}")
            
            stats = result.get("stats", {})
            indexed_files = stats.get("indexed_files", 0)
            total_dirs = stats.get("total_dirs", 0)
            
            print(f"Indexed {indexed_files} files in {total_dirs} directories")
        else:
            print(f"\nFailed to index directory: {result.get('error', 'Unknown error')}")
        
        return result
    
    @staticmethod
    def list(args) -> Dict:
        """
        List indexed directories or vector stores
        
        Args:
            args: Command arguments with type parameter
            
        Returns:
            Result information
        """
        list_type = args.type or "all"
        
        if list_type == "dirs" or list_type == "all":
            print("\nIndexed Directories:")
            directories = file_search_manager.get_indexed_directories()
            
            if not directories:
                print("  No directories indexed yet")
            else:
                for i, directory in enumerate(directories, 1):
                    print(f"  {i}. {directory}")
        
        if list_type == "stores" or list_type == "all":
            print("\nVector Stores:")
            stores = file_search_manager.get_vector_stores()
            
            if not stores:
                print("  No vector stores created yet")
            else:
                for i, store in enumerate(stores, 1):
                    print(f"  {i}. {store['name']} (ID: {store['id']})")
                    print(f"     Files: {store['file_count']}")
                    dirs = store.get('directories', [])
                    if dirs:
                        print(f"     Directories: {len(dirs)}")
                        for j, directory in enumerate(dirs, 1):
                            print(f"       {j}. {directory}")
        
        return {"success": True}
    
    @staticmethod
    def remove(args) -> Dict:
        """
        Remove a directory from the index
        
        Args:
            args: Command arguments with directory parameter
            
        Returns:
            Result information
        """
        directory = args.directory
        
        if not directory:
            return {"error": "Directory path is required"}
        
        directory = os.path.abspath(directory)
        success = directory_indexer.remove_directory_index(directory)
        
        if success:
            print(f"\nRemoved directory from index: {directory}")
        else:
            print(f"\nDirectory not found in index: {directory}")
        
        return {"success": success}
    
    @staticmethod
    def search(args) -> Dict:
        """
        Search in indexed directories
        
        Args:
            args: Command arguments with query and vector_store parameters
            
        Returns:
            Search results
        """
        query = args.query
        vector_store = args.vector_store or "default"
        max_results = args.max_results or 5
        
        if not query:
            return {"error": "Search query is required"}
        
        print(f"\nSearching for: {query}")
        print(f"In vector store: {vector_store}")
        
        result = file_search_manager.search(query, vector_store, max_results)
        
        if "error" in result:
            print(f"\nSearch failed: {result['error']}")
            return result
        
        print("\nSearch Results:")
        
        response = result.get("response")
        
        if not response:
            print("  No results found")
            return {"success": True, "results": []}
        
        # Process and display the search results
        try:
            result_shown = False
            
            if hasattr(response, 'output'):
                for output_item in response.output:
                    if hasattr(output_item, 'type') and output_item.type == "message":
                        if hasattr(output_item, 'content') and output_item.content:
                            content = output_item.content[0]
                            if hasattr(content, 'text'):
                                print(f"\n{content.text}")
                                result_shown = True
                    
                    if hasattr(output_item, 'type') and output_item.type == "file_search_call":
                        if hasattr(output_item, 'search_results') and output_item.search_results:
                            print("\nDetailed search results:")
                            for i, result in enumerate(output_item.search_results, 1):
                                print(f"  {i}. {result.text[:100]}...")
                                result_shown = True
            
            # No need for additional message since we're already printing results directly
        except Exception as e:
            print(f"\nError processing results: {e}")
        
        return {"success": True}
    
    @staticmethod
    def status(args) -> Dict:
        """
        Show indexing status
        
        Args:
            args: Command arguments
            
        Returns:
            Status information
        """
        print("\nIndexing Status:")
        
        summary = directory_indexer.get_index_summary()
        
        if "status" in summary and summary["status"] == "No indexed directories":
            print("  No directories indexed yet")
            return {"success": True}
        
        print(f"  Indexed directories: {summary['indexed_directories']}")
        print(f"  Total directories: {summary['total_directories']}")
        print(f"  Total files: {summary['total_files']}")
        print(f"  Total size: {summary['total_size_mb']:.2f} MB")
        
        # Show information about each indexed directory
        print("\nIndexed Directories Detail:")
        for dir_path in directory_indexer.get_indexed_directories():
            dir_info = directory_indexer.get_directory_index(dir_path)
            if dir_info:
                file_count = len(dir_info.get("files", []))
                dir_count = len(dir_info.get("directories", []))
                print(f"\n  Directory: {dir_path}")
                print(f"    Files: {file_count}")
                print(f"    Subdirectories: {dir_count}")
                
                # Show file types distribution
                if file_count > 0:
                    file_types = {}
                    for file in dir_info.get("files", []):
                        file_type = file.get("category", "unknown")
                        if file_type not in file_types:
                            file_types[file_type] = 0
                        file_types[file_type] += 1
                    
                    print(f"    File types:")
                    for file_type, count in sorted(file_types.items(), key=lambda x: x[1], reverse=True):
                        print(f"      {file_type}: {count}")
                    
                    # Show some sample files
                    print(f"\n    Sample files (first 5):")
                    for i, file in enumerate(dir_info.get("files", [])[:5], 1):
                        print(f"      {i}. {file.get('name', 'Unknown')}")
        
        return {"success": True}
    
    @staticmethod
    def clear(args) -> Dict:
        """
        Clear all indices
        
        Args:
            args: Command arguments
            
        Returns:
            Result information
        """
        if not args.force:
            confirm = input("\nAre you sure you want to clear all indices? This cannot be undone. (y/N): ")
            if confirm.lower() != 'y':
                print("Operation cancelled")
                return {"success": False}
        
        success = directory_indexer.clear_index()
        
        if success:
            print("\nAll indices cleared successfully")
        else:
            print("\nFailed to clear indices")
        
        return {"success": success}

def setup_parser(subparsers):
    """
    Set up the command-line parser for file search commands
    
    Args:
        subparsers: Subparsers object from argparse
    """
    # Index command
    parser_index = subparsers.add_parser('index', help='Index a directory')
    parser_index.add_argument('directory', help='Directory to index')
    parser_index.add_argument('--vector-store', help='Vector store name (default: "default")')
    parser_index.add_argument('--max-depth', type=int, default=3, help='Maximum depth to traverse')
    parser_index.set_defaults(func=FileSearchCommands.index)
    
    # List command
    parser_list = subparsers.add_parser('list', help='List indexed directories or vector stores')
    parser_list.add_argument('--type', choices=['dirs', 'stores', 'all'], help='Type of listing (default: "all")')
    parser_list.set_defaults(func=FileSearchCommands.list)
    
    # Remove command
    parser_remove = subparsers.add_parser('remove', help='Remove a directory from the index')
    parser_remove.add_argument('directory', help='Directory to remove')
    parser_remove.set_defaults(func=FileSearchCommands.remove)
    
    # Search command
    parser_search = subparsers.add_parser('search', help='Search in indexed directories')
    parser_search.add_argument('query', help='Search query')
    parser_search.add_argument('--vector-store', help='Vector store name (default: "default")')
    parser_search.add_argument('--max-results', type=int, help='Maximum number of results (default: 5)')
    parser_search.set_defaults(func=FileSearchCommands.search)
    
    # Status command
    parser_status = subparsers.add_parser('status', help='Show indexing status')
    parser_status.set_defaults(func=FileSearchCommands.status)
    
    # Clear command
    parser_clear = subparsers.add_parser('clear', help='Clear all indices')
    parser_clear.add_argument('--force', action='store_true', help='Skip confirmation prompt')
    parser_clear.set_defaults(func=FileSearchCommands.clear)