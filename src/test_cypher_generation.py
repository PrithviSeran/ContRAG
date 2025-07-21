#!/usr/bin/env python3
"""
Test script to debug Cypher query generation
"""

import os
from dotenv import load_dotenv
from license_pipeline_runner import LicenseGraphRAGPipeline

load_dotenv()

def test_cypher_generation():
    """Test what Cypher query is being generated for a simple question"""
    
    print("🧪 TESTING CYPHER QUERY GENERATION")
    print("="*50)
    
    try:
        pipeline = LicenseGraphRAGPipeline()
        
        # Test question
        test_question = "give me a summary of the license contracts"
        
        print(f"🔍 Testing question: {test_question}")
        
        # Get the generated Cypher query
        cypher_query = pipeline._generate_cypher_query(test_question, limit=10)
        print(f"📝 Generated Cypher query:")
        print(cypher_query)
        print("\n" + "="*50)
        
        # Test the query directly
        print("🔍 Testing the generated query...")
        with pipeline.driver.session() as session:
            result = session.run(cypher_query)
            contracts = []
            
            for record in result:
                contract = {
                    'title': record.get('title'),
                    'contract_type': record.get('contract_type'),
                    'summary': record.get('summary'),
                    'execution_date': str(record['execution_date']) if record.get('execution_date') else None,
                    'effective_date': str(record['effective_date']) if record.get('effective_date') else None,
                    'upfront_payment': record.get('upfront_payment'),
                    'exclusivity_grant_type': record.get('exclusivity_grant_type'),
                    'oem_type': record.get('oem_type'),
                    'licensed_field_of_use': record.get('licensed_field_of_use'),
                    'governing_law': record.get('governing_law'),
                    'jurisdiction': record.get('jurisdiction'),
                    'licensors': [l for l in record.get('licensors', []) if l and l.get('name')],
                    'licensees': [le for le in record.get('licensees', []) if le and le.get('name')],
                    'patents': [p for p in record.get('patents', []) if p and p.get('patent_number')],
                    'products': [pr for pr in record.get('products', []) if pr and pr.get('product_name')],
                    'territories': [t for t in record.get('territories', []) if t and t.get('territory_name')]
                }
                contracts.append(contract)
            
            print(f"📊 Retrieved {len(contracts)} contracts from generated query")
            
            # Check if contracts have data
            null_count = 0
            total_fields = 0
            
            for i, contract in enumerate(contracts[:3]):  # Check first 3 contracts
                print(f"\nContract {i+1}:")
                for key, value in contract.items():
                    total_fields += 1
                    if value is None or (isinstance(value, list) and len(value) == 0):
                        null_count += 1
                        print(f"  ❌ {key}: {value}")
                    else:
                        print(f"  ✅ {key}: {value}")
            
            print(f"\n📊 Summary: {null_count}/{total_fields} fields are null")
            
        pipeline.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_cypher_generation() 