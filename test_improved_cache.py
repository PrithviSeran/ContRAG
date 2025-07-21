#!/usr/bin/env python3
"""
Test script to demonstrate the improved cache structure
"""

import os
import json
from batch_ingest_license_contracts import EnhancedLicenseBatchProcessor

def test_improved_cache():
    """Test the improved cache structure"""
    
    print("🧪 TESTING IMPROVED CACHE STRUCTURE")
    print("="*50)
    
    # Initialize the processor
    processor = EnhancedLicenseBatchProcessor()
    
    # Load existing cache
    print("📁 Loading existing cache...")
    processor.load_processed_cache()
    
    # Show cache statistics
    print(f"📊 Cache contains {len(processor.processed_data_cache)} contracts")
    
    # Analyze cache structure
    new_format_count = 0
    old_format_count = 0
    
    for file_path, cached_data in processor.processed_data_cache.items():
        if 'contract' in cached_data:
            new_format_count += 1
        else:
            old_format_count += 1
    
    print(f"📋 Cache format analysis:")
    print(f"   New format (full structure): {new_format_count}")
    print(f"   Old format (simplified): {old_format_count}")
    
    # Show example of new cache structure
    if new_format_count > 0:
        print(f"\n📄 Example of new cache structure:")
        for file_path, cached_data in processor.processed_data_cache.items():
            if 'contract' in cached_data:
                contract = cached_data['contract']
                print(f"\n   File: {os.path.basename(file_path)}")
                print(f"   Title: {contract.get('title', 'Unknown')}")
                print(f"   Type: {contract.get('contract_type', 'Unknown')}")
                
                # Show detailed party information
                licensor = contract.get('licensor', {})
                licensee = contract.get('licensee', {})
                print(f"   Licensor: {licensor.get('name', 'Unknown')}")
                print(f"     Address: {licensor.get('address', 'Not specified')}")
                print(f"     Entity Type: {licensor.get('entity_type', 'Not specified')}")
                print(f"     Jurisdiction: {licensor.get('jurisdiction', 'Not specified')}")
                
                print(f"   Licensee: {licensee.get('name', 'Unknown')}")
                print(f"     Address: {licensee.get('address', 'Not specified')}")
                print(f"     Entity Type: {licensee.get('entity_type', 'Not specified')}")
                print(f"     Jurisdiction: {licensee.get('jurisdiction', 'Not specified')}")
                
                # Show licensed materials
                patents = contract.get('licensed_patents', [])
                products = contract.get('licensed_products', [])
                territories = contract.get('licensed_territory', [])
                
                print(f"   Patents ({len(patents)}):")
                for patent in patents[:2]:  # Show first 2
                    print(f"     - {patent.get('patent_number', 'Unknown')}: {patent.get('patent_title', 'No title')}")
                
                print(f"   Products ({len(products)}):")
                for product in products[:2]:  # Show first 2
                    print(f"     - {product.get('product_name', 'Unknown')}: {product.get('description', 'No description')}")
                
                print(f"   Territories ({len(territories)}):")
                for territory in territories[:2]:  # Show first 2
                    print(f"     - {territory.get('territory_name', 'Unknown')} ({territory.get('territory_type', 'Unknown type')})")
                
                # Show financial and legal information
                print(f"   Financial Terms:")
                print(f"     Upfront Payment: ${contract.get('upfront_payment', 0):,.2f}" if contract.get('upfront_payment') else "     Upfront Payment: Not specified")
                print(f"     Stacking Clause: {contract.get('stacking_clause_indicator', 'Not specified')}")
                print(f"     Most Favored Nations: {contract.get('most_favored_nations_clause', 'Not specified')}")
                
                print(f"   Legal Provisions:")
                print(f"     Governing Law: {contract.get('governing_law', 'Not specified')}")
                print(f"     Jurisdiction: {contract.get('jurisdiction', 'Not specified')}")
                print(f"     Assignment Restrictions: {contract.get('assignment_restrictions', 'Not specified')}")
                
                # Show additional rich data
                if contract.get('warranties_litigation'):
                    print(f"     Warranties (Litigation): {contract.get('warranties_litigation', 'Not specified')}")
                if contract.get('confidential_agreement'):
                    print(f"     Confidentiality: {contract.get('confidential_agreement', 'Not specified')}")
                
                break  # Show only first example
    
    # Test cache save with new structure
    print(f"\n💾 Testing cache save with new structure...")
    processor.save_processed_cache(force_backup=True)
    
    print(f"\n✅ Improved cache structure test completed!")
    print(f"🎯 Benefits of new cache structure:")
    print(f"   ✅ Preserves all extracted data")
    print(f"   ✅ Enables rich querying and analytics")
    print(f"   ✅ Maintains data integrity")
    print(f"   ✅ Supports advanced contract analysis")

if __name__ == "__main__":
    test_improved_cache() 