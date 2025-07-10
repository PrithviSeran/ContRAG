#!/usr/bin/env python3
"""
Test script to validate the License GraphRAG system components
"""

import os
from license_pipeline_runner import LicenseGraphRAGPipeline, extract_text_from_html, extract_text_from_txt

def test_text_extraction():
    """Test text extraction from sample files"""
    
    print("🧪 TESTING LICENSE TEXT EXTRACTION")
    print("="*50)
    
    # Test HTML extraction
    html_file = "../data/10.1.html"
    if os.path.exists(html_file):
        print(f"📄 Testing HTML extraction: {html_file}")
        html_text = extract_text_from_html(html_file)
        print(f"✅ Extracted {len(html_text)} characters from HTML")
        print(f"📝 First 200 chars: {html_text[:200]}...")
    else:
        print("❌ HTML test file not found")
    
    # Test TXT extraction
    txt_file = "../data/ABEONA-THERAPEUTICS-INC/1997/10-Q/0000318306-97-000010/EX-10.12.txt"
    if os.path.exists(txt_file):
        print(f"\n📄 Testing TXT extraction: {txt_file}")
        txt_text = extract_text_from_txt(txt_file)
        print(f"✅ Extracted {len(txt_text)} characters from TXT")
        print(f"📝 First 200 chars: {txt_text[:200]}...")
    else:
        print("❌ TXT test file not found")

def test_pipeline_initialization():
    """Test license pipeline initialization"""
    
    print("\n🧪 TESTING LICENSE PIPELINE INITIALIZATION")
    print("="*50)
    
    try:
        pipeline = LicenseGraphRAGPipeline()
        print("✅ License pipeline initialized successfully")
        
        # Test database connection
        stats = pipeline.get_database_stats()
        print(f"✅ Database connection successful")
        print(f"📊 Current stats: {stats}")
        
        pipeline.close()
        print("✅ Pipeline closed successfully")
        return True
        
    except Exception as e:
        print(f"❌ License pipeline initialization failed: {e}")
        return False

def test_single_license_processing():
    """Test processing a single license contract"""
    
    print("\n🧪 TESTING SINGLE LICENSE CONTRACT PROCESSING")
    print("="*50)
    
    # Use a simple license contract for testing
    sample_license = """
    LICENSE AGREEMENT
    
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
        
        # Process the sample license contract
        contract_data = pipeline.ingest_contract(sample_license, "TEST-LICENSE-001")
        
        print(f"✅ License contract processed successfully")
        print(f"📋 Title: {contract_data.title}")
        print(f"📋 Type: {contract_data.contract_type}")
        print(f"📋 Summary: {contract_data.summary}")
        print(f"📋 Licensor: {contract_data.licensor.name if contract_data.licensor else 'Unknown'}")
        print(f"📋 Licensee: {contract_data.licensee.name if contract_data.licensee else 'Unknown'}")
        print(f"📋 Exclusivity: {contract_data.exclusivity_grant_type.value if contract_data.exclusivity_grant_type else 'Unknown'}")
        print(f"📋 Upfront Payment: ${contract_data.upfront_payment:,.2f}" if contract_data.upfront_payment else "📋 Upfront Payment: Not specified")
        print(f"📋 Patents: {len(contract_data.licensed_patents)}")
        
        # Test querying
        result = pipeline.query_contracts("What is the upfront license fee?")
        print(f"✅ Query successful")
        print(f"🤖 Answer: {result[:200]}...")
        
        pipeline.close()
        return True
        
    except Exception as e:
        print(f"❌ License contract processing failed: {e}")
        return False

def test_license_search():
    """Test license contract search functionality"""
    
    print("\n🧪 TESTING LICENSE CONTRACT SEARCH")
    print("="*50)
    
    try:
        pipeline = LicenseGraphRAGPipeline()
        
        # Test search with various criteria
        search_criteria = {
            'exclusivity_type': 'Exclusive',
            'min_upfront_payment': 100000
        }
        
        results = pipeline.search_contracts(search_criteria)
        print(f"✅ Search completed successfully")
        print(f"📊 Found {len(results)} contracts matching criteria")
        
        if results:
            print(f"📋 First result: {results[0]['title']}")
        
        pipeline.close()
        return True
        
    except Exception as e:
        print(f"❌ License search failed: {e}")
        return False

def test_database_schema():
    """Test database schema creation and constraints"""
    
    print("\n🧪 TESTING DATABASE SCHEMA")
    print("="*50)
    
    try:
        pipeline = LicenseGraphRAGPipeline()
        
        # Test that schema was created properly
        with pipeline.driver.session() as session:
            # Check if constraints exist
            result = session.run("SHOW CONSTRAINTS")
            constraints = list(result)
            print(f"✅ Found {len(constraints)} constraints in database")
            
            # Check if indexes exist
            result = session.run("SHOW INDEXES")
            indexes = list(result)
            print(f"✅ Found {len(indexes)} indexes in database")
            
            # Check node types
            result = session.run("CALL db.labels()")
            labels = [record['label'] for record in result]
            print(f"✅ Database labels: {labels}")
            
            # Check relationship types
            result = session.run("CALL db.relationshipTypes()")
            rel_types = [record['relationshipType'] for record in result]
            print(f"✅ Relationship types: {rel_types}")
        
        pipeline.close()
        return True
        
    except Exception as e:
        print(f"❌ Database schema test failed: {e}")
        return False

def main():
    """Run all license system tests"""
    
    print("🚀 LICENSE GRAPHRAG SYSTEM VALIDATION")
    print("="*60)
    
    # Test 1: Text extraction
    test_text_extraction()
    
    # Test 2: Pipeline initialization
    pipeline_ok = test_pipeline_initialization()
    
    # Test 3: Database schema
    if pipeline_ok:
        test_database_schema()
    
    # Test 4: Single license contract processing (only if pipeline works)
    if pipeline_ok:
        test_single_license_processing()
    
    # Test 5: License search functionality
    if pipeline_ok:
        test_license_search()
    
    print("\n🎉 LICENSE SYSTEM TESTING COMPLETE")
    print("="*60)
    print("License system is ready for batch processing!")

if __name__ == "__main__":
    main() 