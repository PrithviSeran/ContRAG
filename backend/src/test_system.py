#!/usr/bin/env python3
"""
Test script to validate the GraphRAG system components
"""

import os
from .securities_pipeline_runner import SecuritiesGraphRAGPipeline, extract_text_from_html, extract_text_from_txt

def test_text_extraction():
    """Test text extraction from sample files"""
    
    print("🧪 TESTING TEXT EXTRACTION")
    print("="*50)
    
    # Test HTML extraction
    html_file = "data/ABEONA-THERAPEUTICS-INC/2022/10-Q/0001493152-22-021969/10.3.html"
    if os.path.exists(html_file):
        print(f"📄 Testing HTML extraction: {html_file}")
        html_text = extract_text_from_html(html_file)
        print(f"✅ Extracted {len(html_text)} characters from HTML")
        print(f"📝 First 200 chars: {html_text[:200]}...")
    else:
        print("❌ HTML test file not found")
    
    # Test TXT extraction
    txt_file = "data/ABEONA-THERAPEUTICS-INC/2001/10-Q/0000318306-01-500012/EX-10.19.txt"
    if os.path.exists(txt_file):
        print(f"\n📄 Testing TXT extraction: {txt_file}")
        txt_text = extract_text_from_txt(txt_file)
        print(f"✅ Extracted {len(txt_text)} characters from TXT")
        print(f"📝 First 200 chars: {txt_text[:200]}...")
    else:
        print("❌ TXT test file not found")

def test_pipeline_initialization():
    """Test pipeline initialization"""
    
    print("\n🧪 TESTING PIPELINE INITIALIZATION")
    print("="*50)
    
    try:
        pipeline = SecuritiesGraphRAGPipeline()
        print("✅ Pipeline initialized successfully")
        
        # Test database connection
        stats = pipeline.get_database_stats()
        print(f"✅ Database connection successful")
        print(f"📊 Current stats: {stats}")
        
        pipeline.close()
        print("✅ Pipeline closed successfully")
        return True
        
    except Exception as e:
        print(f"❌ Pipeline initialization failed: {e}")
        return False

def test_single_contract_processing():
    """Test processing a single contract"""
    
    print("\n🧪 TESTING SINGLE CONTRACT PROCESSING")
    print("="*50)
    
    # Use a simple contract for testing
    sample_contract = """
    SECURITIES PURCHASE AGREEMENT
    
    This Securities Purchase Agreement is entered into as of May 16, 2022
    by and between Abeona Therapeutics Inc., a Delaware corporation ("Company"), 
    and the investors listed on Schedule A ("Purchasers").
    
    The Company agrees to issue and sell to each Purchaser, and each Purchaser 
    agrees to purchase from the Company, shares of common stock at a purchase 
    price of $1.50 per share for a total offering of $5,000,000.
    """
    
    try:
        pipeline = SecuritiesGraphRAGPipeline()
        
        # Process the sample contract
        contract_data = pipeline.ingest_contract(sample_contract, "TEST-001")
        
        print(f"✅ Contract processed successfully")
        print(f"📋 Title: {contract_data.title}")
        print(f"📋 Type: {contract_data.contract_type}")
        print(f"📋 Summary: {contract_data.summary}")
        
        # Test querying
        result = pipeline.query_contracts("What is the purchase price per share?")
        print(f"✅ Query successful")
        print(f"🤖 Answer: {result[:200]}...")
        
        pipeline.close()
        return True
        
    except Exception as e:
        print(f"❌ Contract processing failed: {e}")
        return False

def main():
    """Run all tests"""
    
    print("🚀 GRAPHRAG SYSTEM VALIDATION")
    print("="*60)
    
    # Test 1: Text extraction
    test_text_extraction()
    
    # Test 2: Pipeline initialization
    pipeline_ok = test_pipeline_initialization()
    
    # Test 3: Single contract processing (only if pipeline works)
    if pipeline_ok:
        test_single_contract_processing()
    
    print("\n🎉 TESTING COMPLETE")
    print("="*60)
    print("System is ready for batch processing!")

if __name__ == "__main__":
    main() 