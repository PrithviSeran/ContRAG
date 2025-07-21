#!/usr/bin/env python3
"""
Interactive test script for the improved RAG system
"""

import os
from license_pipeline_runner import LicenseGraphRAGPipeline

def interactive_test():
    """Interactive test of the RAG system"""
    
    print("🤖 INTERACTIVE RAG SYSTEM TEST")
    print("="*50)
    print("This will test the improved Cypher query generation.")
    print("Type 'quit' to exit.\n")
    
    # Initialize the pipeline
    pipeline = LicenseGraphRAGPipeline()
    
    while True:
        try:
            # Get user query
            query = input("\n🔍 Enter your question about license contracts: ").strip()
            
            if query.lower() in ['quit', 'exit', 'q']:
                break
            
            if not query:
                print("Please enter a question.")
                continue
            
            print(f"\n📝 Processing: {query}")
            print("-" * 40)
            
            # Test the query
            try:
                # Generate Cypher query
                cypher_query = pipeline._generate_cypher_query(query, limit=5)
                print(f"✅ Generated Cypher query:")
                print(f"   {cypher_query}")
                
                # Get relevant contracts
                contracts = pipeline._get_relevant_contracts(query, limit=5)
                print(f"\n📊 Retrieved {len(contracts)} relevant contracts")
                
                # Show sample results
                if contracts:
                    print(f"\n📋 Sample results:")
                    for i, contract in enumerate(contracts[:3], 1):
                        print(f"   {i}. {contract.get('title', 'No title')}")
                        if contract.get('summary'):
                            print(f"      Summary: {contract['summary'][:100]}...")
                        if contract.get('licensors'):
                            print(f"      Licensor: {contract['licensors'][0].get('name', 'Unknown')}")
                        print()
                
            except Exception as e:
                print(f"❌ Error: {e}")
                print("The system will use fallback queries for this question.")
        
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
            break
    
    pipeline.close()
    print("✅ Test completed!")

if __name__ == "__main__":
    interactive_test() 