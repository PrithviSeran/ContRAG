#!/usr/bin/env python3
"""
Test script to verify improved Cypher query generation
"""

import os
from license_pipeline_runner import LicenseGraphRAGPipeline

def test_query_generation():
    """Test the improved Cypher query generation"""
    
    print("🧪 TESTING IMPROVED CYPHER QUERY GENERATION")
    print("="*60)
    
    # Initialize the pipeline
    pipeline = LicenseGraphRAGPipeline()
    
    # Test different types of queries
    test_queries = [
        "Show me all exclusive license agreements",
        "Find contracts with upfront payments over $1 million",
        "What license agreements involve patent 9,876,543?",
        "Show me contracts from TechCorp Inc.",
        "Find license agreements in California"
    ]
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n🔍 Test {i}: {query}")
        print("-" * 40)
        
        try:
            # Test query generation
            cypher_query = pipeline._generate_cypher_query(query, limit=5)
            print(f"✅ Generated Cypher query:")
            print(f"   {cypher_query[:200]}...")
            
            # Test contract retrieval
            contracts = pipeline._get_relevant_contracts(query, limit=5)
            print(f"✅ Retrieved {len(contracts)} contracts")
            
        except Exception as e:
            print(f"❌ Error: {e}")
    
    print(f"\n🎉 Query generation test completed!")
    pipeline.close()

if __name__ == "__main__":
    test_query_generation() 