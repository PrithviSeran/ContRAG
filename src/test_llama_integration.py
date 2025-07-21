#!/usr/bin/env python3
"""
Test script to verify Llama 3.3 70B integration
"""

import os
from dotenv import load_dotenv
from license_extraction import LicenseContractExtractor

load_dotenv()

def test_llama_extraction():
    """Test Llama-based contract extraction"""
    
    print("🧪 TESTING LLAMA 3.3 70B INTEGRATION")
    print("="*50)
    
    # Get model path
    model_path = os.getenv("LLAMA_MODEL_PATH", "/path/to/llama-3.3-70b")
    
    if not os.path.exists(model_path):
        print(f"❌ Llama model not found at: {model_path}")
        print("Please set LLAMA_MODEL_PATH environment variable to the correct path")
        return False
    
    try:
        print(f"🔧 Loading Llama model from: {model_path}")
        extractor = LicenseContractExtractor(model_path=model_path)
        print("✅ Llama model loaded successfully")
        
        # Test with a sample license contract
        sample_contract = """
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
        
        print("🔍 Testing contract extraction...")
        contract_data = extractor.extract_contract_data(sample_contract)
        
        print("✅ Contract extraction successful!")
        print(f"📋 Title: {contract_data.title}")
        print(f"📋 Type: {contract_data.contract_type}")
        print(f"📋 Summary: {contract_data.summary}")
        print(f"📋 Licensor: {contract_data.licensor.name if contract_data.licensor else 'Unknown'}")
        print(f"📋 Licensee: {contract_data.licensee.name if contract_data.licensee else 'Unknown'}")
        print(f"📋 Exclusivity: {contract_data.exclusivity_grant_type.value if contract_data.exclusivity_grant_type else 'Unknown'}")
        print(f"📋 Upfront Payment: ${contract_data.upfront_payment:,.2f}" if contract_data.upfront_payment else "📋 Upfront Payment: Not specified")
        print(f"📋 Patents: {len(contract_data.licensed_patents)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Llama integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_pipeline_initialization():
    """Test pipeline initialization with Llama"""
    
    print("\n🧪 TESTING PIPELINE INITIALIZATION")
    print("="*50)
    
    try:
        from license_pipeline_runner import LicenseGraphRAGPipeline
        
        model_path = os.getenv("LLAMA_MODEL_PATH", "/path/to/llama-3.3-70b")
        pipeline = LicenseGraphRAGPipeline(model_path=model_path)
        
        print("✅ Pipeline initialized successfully with Llama")
        
        # Test database connection
        stats = pipeline.get_database_stats()
        print(f"✅ Database connection successful")
        print(f"📊 Current stats: {stats}")
        
        pipeline.close()
        print("✅ Pipeline closed successfully")
        return True
        
    except Exception as e:
        print(f"❌ Pipeline initialization failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all Llama integration tests"""
    
    print("🚀 LLAMA 3.3 70B INTEGRATION TESTING")
    print("="*60)
    
    # Test 1: Basic extraction
    extraction_ok = test_llama_extraction()
    
    # Test 2: Pipeline initialization
    if extraction_ok:
        pipeline_ok = test_pipeline_initialization()
    else:
        pipeline_ok = False
    
    print(f"\n🎉 LLAMA INTEGRATION TESTING COMPLETE")
    print("="*60)
    
    if extraction_ok and pipeline_ok:
        print("✅ All tests passed! Llama integration is working correctly.")
        print("\n📋 Next steps:")
        print("1. Set LLAMA_MODEL_PATH environment variable to your model path")
        print("2. Run batch_ingest_license_contracts.py to process contracts")
        print("3. Test live QA sessions with the new Llama-based system")
    else:
        print("❌ Some tests failed. Please check the error messages above.")
        print("\n🔧 Troubleshooting:")
        print("1. Ensure LLAMA_MODEL_PATH points to the correct model directory")
        print("2. Verify the model files are accessible")
        print("3. Check that you have sufficient GPU memory for the 70B model")

if __name__ == "__main__":
    main() 