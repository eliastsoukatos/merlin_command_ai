#!/usr/bin/env python3
"""
Merlin Files - Command-line tool for indexing and searching files using OpenAI's file search API.
"""

import argparse
import sys
from src.commands.file_search_commands import setup_parser, FileSearchCommands

def main():
    """Main entry point for the Merlin Files CLI tool"""
    
    # Create the main parser
    parser = argparse.ArgumentParser(
        description='Merlin Files - Index and search your files with AI',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Index a directory
  merlin_files index ~/Documents
  
  # Index a directory with a specific vector store name
  merlin_files index ~/Documents --vector-store my_docs
  
  # List indexed directories
  merlin_files list --type dirs
  
  # Search in indexed directories
  merlin_files search "find all Python files related to machine learning"
  
  # Show indexing status
  merlin_files status
  
  # Remove a directory from the index
  merlin_files remove ~/Documents
  
  # Clear all indices
  merlin_files clear
"""
    )
    
    # Create subparsers for commands
    subparsers = parser.add_subparsers(dest='command', help='Command to run')
    
    # Set up command parsers
    setup_parser(subparsers)
    
    # Parse arguments
    args = parser.parse_args()
    
    # Execute the appropriate command
    if args.command:
        if hasattr(args, 'func'):
            args.func(args)
        else:
            parser.print_help()
    else:
        parser.print_help()

if __name__ == '__main__':
    main()