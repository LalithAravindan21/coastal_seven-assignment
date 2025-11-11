#!/usr/bin/env python3
"""
Command-line interface for the Multimodal Query System
"""

import argparse
import sys
import os
from database import KnowledgeBase
from processor import FileProcessor
from query_engine import QueryEngine
from processors.audio_video_processor import AudioVideoProcessor
from config import GEMINI_API_KEY

def main():
    parser = argparse.ArgumentParser(description='Multimodal Query System - CLI')
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Process command
    process_parser = subparsers.add_parser('process', help='Process a file or YouTube URL')
    process_parser.add_argument('input', help='File path or YouTube URL')
    
    # Query command
    query_parser = subparsers.add_parser('query', help='Query the knowledge base')
    query_parser.add_argument('question', help='Your question')
    
    # List command
    list_parser = subparsers.add_parser('list', help='List all processed files')
    
    # Clear command
    clear_parser = subparsers.add_parser('clear', help='Clear all data from database')
    clear_parser.add_argument('--confirm', action='store_true', help='Confirm deletion')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # Check API key
    if not GEMINI_API_KEY:
        print("ERROR: GEMINI_API_KEY not found. Please create a .env file with your API key.")
        print("Get your API key from: https://makersuite.google.com/app/apikey")
        sys.exit(1)
    
    # Initialize components
    db = KnowledgeBase()
    processor = FileProcessor(db)
    
    try:
        query_engine = QueryEngine(db)
    except Exception as e:
        print(f"ERROR: Failed to initialize query engine: {e}")
        sys.exit(1)
    
    # Handle commands
    if args.command == 'process':
        print(f"Processing: {args.input}")
        
        av_processor = AudioVideoProcessor()
        if av_processor.is_youtube_url(args.input):
            result = processor.process_youtube(args.input)
        else:
            if not os.path.exists(args.input):
                print(f"ERROR: File not found: {args.input}")
                sys.exit(1)
            result = processor.process_file(args.input)
        
        if result['success']:
            print(f"SUCCESS: {result['message']}")
            print(f"Chunks created: {result.get('chunks_count', 0)}")
        else:
            print(f"ERROR: {result['message']}")
            sys.exit(1)
    
    elif args.command == 'query':
        print(f"Question: {args.question}")
        print("\nSearching knowledge base...\n")
        
        response = query_engine.query(args.question)
        print("Answer:")
        print("-" * 50)
        print(response)
        print("-" * 50)
        
        # Save query
        db.save_query(args.question, response)
    
    elif args.command == 'list':
        files = db.get_all_files()
        if not files:
            print("No files processed yet.")
        else:
            print(f"\nProcessed Files ({len(files)}):")
            print("-" * 50)
            for file_info in files:
                status = "✓" if file_info['processed'] else "✗"
                print(f"{status} {file_info['filename']} ({file_info['file_type']})")
                print(f"   Uploaded: {file_info['upload_date']}")
            print("-" * 50)
    
    elif args.command == 'clear':
        if not args.confirm:
            print("WARNING: This will delete all processed data!")
            print("Use --confirm flag to proceed.")
            sys.exit(1)
        
        if os.path.exists("knowledge_base.db"):
            os.remove("knowledge_base.db")
            print("Database cleared successfully!")
        else:
            print("No database found.")

if __name__ == '__main__':
    main()

