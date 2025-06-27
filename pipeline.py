#!/usr/bin/env python3
"""
Simple ABEONA GraphRAG Pipeline
Run from project root: python pipeline.py
"""

import os
import sys
from dotenv import load_dotenv

# Handle running from either root directory or src directory
if os.path.basename(os.getcwd()) == 'src':
    # Running from src directory
    sys.path.insert(0, '.')
    data_path = "../data/ABEONA-THERAPEUTICS-INC"
    env_path = "../.env"
else:
    # Running from root directory  
    sys.path.insert(0, 'src')
    data_path = "data/ABEONA-THERAPEUTICS-INC"
    env_path = ".env"

from batch_ingest_contracts import EnhancedBatchProcessor

def main():
    """Simple pipeline - process contracts and start interactive session."""
    
    # Load environment variables
    load_dotenv(env_path)
    
    print("🚀 ABEONA GraphRAG Pipeline")
    print("=" * 40)
    
    # Set up the data path
    os.environ["ABEONA_DATA_PATH"] = data_path
    print(f"📁 Looking for contracts in: {os.path.abspath(data_path)}")
    
    # Create the processor
    processor = EnhancedBatchProcessor()
    
    print("📄 Processing contracts...")
    
    # Process all contracts
    try:
        report = processor.run_batch_processing()
        
        # Show results
        print("\n" + "=" * 50)
        print("🎉 PROCESSING COMPLETE!")
        print("=" * 50)
        
        summary = report.get("summary", {})
        print(f"✅ Successfully processed: {summary.get('successfully_processed', 0)} contracts")
        print(f"❌ Failed: {summary.get('failed', 0)} contracts")
        print(f"📊 Total files found: {summary.get('total_files', 0)}")
        
        # Start interactive session if contracts were processed
        if summary.get('successfully_processed', 0) > 0:
            print("\n🤖 Starting interactive query session...")
            print("Ask questions about the contracts! Type 'quit' to exit.")
            processor.run_interactive_query_session()
        else:
            print("\n❌ No contracts were processed. Check the error messages above.")
            
    except Exception as e:
        print(f"\n❌ Pipeline failed: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main()) 