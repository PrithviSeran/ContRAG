#!/usr/bin/env python3
"""
Test script to verify that duplicate contract handling is working correctly
"""

import os
from license_pipeline_runner import LicenseGraphRAGPipeline

def test_duplicate_handling():
    """Test that duplicate contracts are handled gracefully"""
    
    print("🧪 TESTING DUPLICATE CONTRACT HANDLING")
    print("="*50)
    
    # Sample license contract
    sample_license = """
    LICENSE AGREEMENT (TEST-LICENSE-001)
    
    This License Agreement is entered into as of January 15, 2023
    by and between TechCorp Inc., a Delaware corporation ("Licensor"), 
    and InnovateTech LLC, a California limited liability company ("Licensee").
    
    The Licensor grants to the Licensee an exclusive license to use 
    Patent No. 9,876,543 for the manufacture and sale of software products
    in the United States and Canada for a period of 10 years.
    
    The Licensee shall pay an upfront license fee of $500,000 and 
    ongoing royalties of 5% of net sales.
    
    The Licensee shall have the right to sublicense the technology
    to third parties with prior written consent of the Licensor.
    """
    
    try:
        pipeline = LicenseGraphRAGPipeline()
        
        print("📝 Attempting to process contract for the first time...")
        contract_data1 = pipeline.ingest_contract(sample_license, "TEST-LICENSE-001")
        print(f"✅ First processing successful: {contract_data1.title}")
        
        print("\n📝 Attempting to process the same contract again...")
        contract_data2 = pipeline.ingest_contract(sample_license, "TEST-LICENSE-001")
        print(f"✅ Second processing handled gracefully: {contract_data2.title}")
        
        print("\n📝 Attempting to process with a different ID...")
        contract_data3 = pipeline.ingest_contract(sample_license, "TEST-LICENSE-002")
        print(f"✅ Different ID processing successful: {contract_data3.title}")
        
        # Test database stats
        stats = pipeline.get_database_stats()
        print(f"\n📊 Database stats: {stats}")
        
        pipeline.close()
        print("\n✅ All duplicate handling tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Duplicate handling test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_duplicate_handling() 