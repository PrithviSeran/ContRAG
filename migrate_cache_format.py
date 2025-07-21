#!/usr/bin/env python3
"""
Utility to migrate cache files from old format to new full structure format
"""

import os
import json
import glob
from datetime import datetime
from batch_ingest_license_contracts import EnhancedLicenseBatchProcessor

def migrate_cache_format():
    """Migrate existing cache files to new format"""
    
    print("🔄 MIGRATING CACHE FORMAT")
    print("="*50)
    
    # Initialize processor
    processor = EnhancedLicenseBatchProcessor()
    
    # Load existing cache
    print("📁 Loading existing cache...")
    processor.load_processed_cache()
    
    # Analyze current cache
    old_format_files = []
    new_format_files = []
    
    for file_path, cached_data in processor.processed_data_cache.items():
        if 'contract' in cached_data:
            new_format_files.append(file_path)
        else:
            old_format_files.append(file_path)
    
    print(f"📊 Cache analysis:")
    print(f"   Old format files: {len(old_format_files)}")
    print(f"   New format files: {len(new_format_files)}")
    
    if len(old_format_files) == 0:
        print("✅ All cache files are already in new format!")
        return
    
    # Create backup of current cache
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = f"cache_migration_backup_{timestamp}.json"
    
    print(f"\n💾 Creating backup: {backup_file}")
    with open(backup_file, 'w', encoding='utf-8') as f:
        json.dump(processor.processed_data_cache, f, indent=2, default=str)
    
    # Migrate old format files
    print(f"\n🔄 Migrating {len(old_format_files)} files to new format...")
    
    migrated_count = 0
    for file_path in old_format_files:
        try:
            old_data = processor.processed_data_cache[file_path]
            
            # Create new format structure
            new_data = {
                'contract': {
                    'title': old_data.get('title', 'Unknown'),
                    'contract_type': old_data.get('contract_type', 'License Agreement'),
                    'summary': old_data.get('summary', ''),
                    'execution_date': old_data.get('execution_date', None),
                    'effective_date': old_data.get('effective_date', None),
                    'upfront_payment': old_data.get('upfront_payment', None),
                    'exclusivity_grant_type': old_data.get('exclusivity_grant_type', None),
                    'oem_type': old_data.get('oem_type', None),
                    
                    # Parties (simplified from old format)
                    'licensor': {
                        'name': old_data.get('licensor_name', 'Unknown'),
                        'address': None,
                        'entity_type': None,
                        'jurisdiction': None,
                        'contact_info': None
                    },
                    'licensee': {
                        'name': old_data.get('licensee_name', 'Unknown'),
                        'address': None,
                        'entity_type': None,
                        'jurisdiction': None,
                        'contact_info': None
                    },
                    
                    # Licensed materials (counts only from old format)
                    'licensed_patents': [],
                    'licensed_products': [],
                    'licensed_territory': [],
                    
                    # All other fields set to None/empty as they weren't in old format
                    'expiration_date': None,
                    'agreement_grants': None,
                    'exclusivity_milestones': [],
                    'right_to_sublicense': None,
                    'sublicense_restrictions': [],
                    'crosslicensing_indicator': None,
                    'licensed_field_of_use': None,
                    'contract_term': None,
                    'contract_term_details': None,
                    'contract_releases': None,
                    'non_compete_covenant_indicator': None,
                    'retained_licensor_rights': None,
                    'product_branding_rights': None,
                    'license_use_restrictions': None,
                    'licensor_obligations': None,
                    'licensor_improvements_clause': None,
                    'licensee_improvements_clause': None,
                    'licensee_right_to_improvements': None,
                    'related_parties_licensor': None,
                    'related_parties_licensee': None,
                    'related_parties_unknown': None,
                    'stacking_clause_indicator': None,
                    'stacking_clause_terms': None,
                    'most_favored_nations_clause': None,
                    'licensee_infringement_indemnities': None,
                    'licensor_product_liability_indemnities': None,
                    'licensee_product_liability_indemnities': None,
                    'delivery_supply': None,
                    'relationship_between_contract_parties_clause': None,
                    'warranties_litigation': None,
                    'warranties_infringement': None,
                    'warranties_ip_sufficiency': None,
                    'warranties_product_or_service': None,
                    'assignment_restrictions': None,
                    'assignment_restrictions_details': None,
                    'insurance_clause_indicator': None,
                    'audit_clause': None,
                    'late_delivery_clauses': None,
                    'diligence_clause': [],
                    'confidential_agreement': None,
                    'confidential_materials': None,
                    'patent_prosecution_responsibilities': None,
                    'suspected_infringement_clause': None,
                    'legal_representative_organization': None,
                    'legal_representative_lawyer': None,
                    'list_of_exhibits_and_attachments_in_contract': [],
                    'governing_law': None,
                    'jurisdiction': None,
                    'termination_rights': None,
                    'dispute_resolution': None,
                    'risk_factors': [],
                    'material_changes': None,
                    'regulatory_requirements': None,
                    'export_control': None
                },
                'metadata': old_data.get('metadata', {}),
                'processed_at': old_data.get('processed_at', datetime.now().isoformat()),
                'mtime': old_data.get('mtime', 0)
            }
            
            # Update cache with new format
            processor.processed_data_cache[file_path] = new_data
            migrated_count += 1
            
            print(f"   ✅ Migrated: {os.path.basename(file_path)}")
            
        except Exception as e:
            print(f"   ❌ Failed to migrate {os.path.basename(file_path)}: {e}")
    
    # Save migrated cache
    print(f"\n💾 Saving migrated cache...")
    processor.save_processed_cache(force_backup=True)
    
    print(f"\n✅ Migration completed!")
    print(f"   Migrated files: {migrated_count}")
    print(f"   Backup created: {backup_file}")
    print(f"   New cache format preserves all future extracted data")

def cleanup_old_backups():
    """Clean up old backup files after migration"""
    
    print("\n🧹 CLEANING UP OLD BACKUP FILES")
    print("="*50)
    
    # Find all backup files
    backup_files = glob.glob("processed_license_contracts_cache_backup_*.json")
    
    if not backup_files:
        print("📁 No backup files found to clean up")
        return
    
    print(f"📁 Found {len(backup_files)} backup files")
    
    # Keep only the 3 most recent backups
    backup_files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
    files_to_remove = backup_files[3:]
    
    if not files_to_remove:
        print("✅ No old backup files to remove")
        return
    
    print(f"🗑️  Removing {len(files_to_remove)} old backup files...")
    
    for old_file in files_to_remove:
        try:
            os.remove(old_file)
            print(f"   ✅ Removed: {old_file}")
        except Exception as e:
            print(f"   ❌ Failed to remove {old_file}: {e}")
    
    print(f"✅ Cleanup completed! Kept {len(backup_files) - len(files_to_remove)} recent backups")

if __name__ == "__main__":
    migrate_cache_format()
    cleanup_old_backups() 