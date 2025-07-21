#!/usr/bin/env python3
"""
Script to clean up cache backup files and test improved caching
"""

import os
import glob
from batch_ingest_license_contracts import EnhancedLicenseBatchProcessor

def cleanup_backups():
    """Clean up all existing backup files"""
    print("🧹 CLEANING UP CACHE BACKUP FILES")
    print("="*50)
    
    # Count existing backup files
    backup_files = glob.glob("processed_license_contracts_cache_backup_*.json")
    print(f"📁 Found {len(backup_files)} backup files")
    
    if backup_files:
        print("📋 Backup files found:")
        for i, file in enumerate(backup_files[:10], 1):  # Show first 10
            print(f"   {i}. {file}")
        if len(backup_files) > 10:
            print(f"   ... and {len(backup_files) - 10} more")
    
    # Use the processor's cleanup method
    processor = EnhancedLicenseBatchProcessor()
    processor.cleanup_all_backups()
    
    # Verify cleanup
    remaining_backups = glob.glob("processed_license_contracts_cache_backup_*.json")
    print(f"\n✅ Cleanup complete. {len(remaining_backups)} backup files remaining")
    
    if remaining_backups:
        print("📋 Remaining backup files:")
        for file in remaining_backups:
            print(f"   - {file}")

def test_improved_caching():
    """Test the improved caching system"""
    print("\n🧪 TESTING IMPROVED CACHING SYSTEM")
    print("="*50)
    
    processor = EnhancedLicenseBatchProcessor()
    
    # Load existing cache
    print("📁 Loading existing cache...")
    processor.load_processed_cache()
    
    # Test cache save (should not create backup if no changes)
    print("\n💾 Testing cache save (no changes)...")
    processor.save_processed_cache()
    
    # Test cache save with force backup
    print("\n💾 Testing cache save (forced backup)...")
    processor.save_processed_cache(force_backup=True)
    
    print("\n✅ Caching test completed!")

if __name__ == "__main__":
    cleanup_backups()
    test_improved_caching() 