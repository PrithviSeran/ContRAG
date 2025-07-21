#!/usr/bin/env python3
"""
Enhanced Batch ingest for all license contracts
Optimized for processing license agreement files effectively
"""

import os
import glob
import time
import json
from datetime import datetime
from typing import List, Dict, Tuple
from license_pipeline_runner import LicenseGraphRAGPipeline, extract_text_from_html, extract_text_from_txt

class EnhancedLicenseBatchProcessor:
    """Enhanced batch processor for license contracts"""
    
    def __init__(self):
        self.pipeline = None
        self.processed_files = []
        self.failed_files = []
        self.start_time = None
        self.processed_data_cache = {}  # Cache for processed contract data
        self.cache_file = "processed_license_contracts_cache.json"
        
        # Initialize pipeline immediately to avoid None errors
        try:
            print("🔧 Attempting to initialize license pipeline...")
            # Get model path from environment or use default
            model_path = os.getenv("LLAMA_MODEL_PATH", "/path/to/llama-3.3-70b")
            self.pipeline = LicenseGraphRAGPipeline(model_path=model_path)
            print("✅ License pipeline initialized in constructor")
        except Exception as e:
            print(f"❌ Error: Could not initialize license pipeline in constructor: {e}")
            print(f"   Error type: {type(e).__name__}")
            import traceback
            print(f"   Traceback: {traceback.format_exc()}")
            self.pipeline = None
        
    def find_all_contract_files(self, base_dir="../data/ABEONA-THERAPEUTICS-INC") -> List[Tuple[str, str]]:
        """Find all license contract files with their types"""
        
        if base_dir is None:
            base_dir = os.getenv("LICENSE_DATA_PATH", "data/license-agreements")
        
        print(f"🔍 Searching for license contract files in: {os.path.abspath(base_dir)}")
        
        contract_files = []
        
        # Check if this is the uploads directory (for frontend uploads)
        is_upload_dir = "uploads" in base_dir
        
        if is_upload_dir:
            # For uploads directory, search non-recursively to avoid duplicates
            print("📁 Detected uploads directory - searching non-recursively")
            for extension in ["*.html", "*.htm", "*.txt", "*.pdf"]:
                pattern = os.path.join(base_dir, extension)
                files = glob.glob(pattern, recursive=False)
                file_type = extension[2:]  # Remove "*."
                for f in files:
                    if os.path.isfile(f):  # Ensure it's actually a file
                        contract_files.append((f, file_type))
        else:
            # For regular data directories, search recursively
            print("📂 Searching recursively in data directory")
            # Find HTML files
            html_pattern = os.path.join(base_dir, "**", "*.html")
            html_files = glob.glob(html_pattern, recursive=True)
            for f in html_files:
                if os.path.isfile(f):  # Ensure it's actually a file
                    contract_files.append((f, "html"))
            
            # Find HTM files  
            htm_pattern = os.path.join(base_dir, "**", "*.htm")
            htm_files = glob.glob(htm_pattern, recursive=True)
            for f in htm_files:
                if os.path.isfile(f):  # Ensure it's actually a file
                    contract_files.append((f, "htm"))
                
            # Find TXT files
            txt_pattern = os.path.join(base_dir, "**", "*.txt")
            txt_files = glob.glob(txt_pattern, recursive=True)
            for f in txt_files:
                if os.path.isfile(f):  # Ensure it's actually a file
                    contract_files.append((f, "txt"))
            
            # Find PDF files (if supported)
            pdf_pattern = os.path.join(base_dir, "**", "*.pdf")
            pdf_files = glob.glob(pdf_pattern, recursive=True)
            for f in pdf_files:
                if os.path.isfile(f):  # Ensure it's actually a file
                    contract_files.append((f, "pdf"))
        
        # Remove duplicates more thoroughly
        # Use both file path and file size for deduplication
        seen = set()
        unique_files = []
        for file_path, file_type in contract_files:
            try:
                # Create a unique identifier using file path and size
                file_size = os.path.getsize(file_path)
                file_identifier = (os.path.basename(file_path), file_size)
                
                if file_identifier not in seen:
                    seen.add(file_identifier)
                    unique_files.append((file_path, file_type))
                else:
                    print(f"⚠️  Skipping duplicate file: {os.path.basename(file_path)}")
            except OSError as e:
                print(f"⚠️  Warning: Could not stat file {file_path}: {e}")
                continue
        
        print(f"📋 Found {len(unique_files)} unique license contract files")
        
        # Sort by year and type for logical processing order
        unique_files.sort(key=lambda x: (self._extract_year(x[0]), x[1]))
        
        return unique_files
    
    def cleanup_all_backups(self):
        """Clean up all existing backup files (use with caution)"""
        try:
            import glob
            backup_files = glob.glob("processed_license_contracts_cache_backup_*.json")
            
            if not backup_files:
                print("📁 No backup files found to clean up")
                return
            
            print(f"🗑️  Found {len(backup_files)} backup files to clean up")
            
            # Keep only the most recent backup
            backup_files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
            files_to_remove = backup_files[1:]  # Keep the most recent one
            
            for old_file in files_to_remove:
                try:
                    os.remove(old_file)
                    print(f"🗑️  Removed: {old_file}")
                except Exception as e:
                    print(f"⚠️  Could not remove {old_file}: {e}")
            
            print(f"✅ Cleanup completed. Kept: {backup_files[0] if backup_files else 'None'}")
            
        except Exception as e:
            print(f"❌ Error during cleanup: {e}")
    
    def load_processed_cache(self) -> bool:
        """Load previously processed license contract data from cache"""
        try:
            if os.path.exists(self.cache_file):
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    self.processed_data_cache = json.load(f)
                print(f"📁 Loaded cache with {len(self.processed_data_cache)} previously processed license contracts")
                return True
            else:
                print("📁 No existing cache file found. Starting fresh.")
                self.processed_data_cache = {}
                return False
        except Exception as e:
            print(f"⚠️ Warning: Could not load cache: {e}")
            print("📁 Starting with empty cache.")
            self.processed_data_cache = {}
            return False
    
    def save_processed_cache(self, force_backup: bool = False):
        """Save processed license contract data to cache"""
        try:
            # Check if cache has actually changed
            cache_changed = False
            if os.path.exists(self.cache_file):
                try:
                    with open(self.cache_file, 'r', encoding='utf-8') as f:
                        old_cache = json.load(f)
                    cache_changed = len(old_cache) != len(self.processed_data_cache)
                except:
                    cache_changed = True  # If we can't read old cache, assume it changed
            else:
                cache_changed = True  # No previous cache file exists
            
            # Save main cache file
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(self.processed_data_cache, f, indent=2, default=str)
            
            # Only create backup if cache changed or forced
            if cache_changed or force_backup:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_file = f"processed_license_contracts_cache_backup_{timestamp}.json"
                with open(backup_file, 'w', encoding='utf-8') as f:
                    json.dump(self.processed_data_cache, f, indent=2, default=str)
                
                print(f"💾 Saved cache with {len(self.processed_data_cache)} processed license contracts")
                print(f"💾 Backup created: {backup_file}")
                
                # Clean up old backup files (keep only last 5)
                self._cleanup_old_backups()
            else:
                print(f"💾 Updated cache with {len(self.processed_data_cache)} processed license contracts (no changes detected)")
                
        except Exception as e:
            print(f"⚠️ Warning: Could not save cache: {e}")
    
    def _cleanup_old_backups(self, keep_count: int = 5):
        """Clean up old backup files, keeping only the most recent ones"""
        try:
            import glob
            backup_files = glob.glob("processed_license_contracts_cache_backup_*.json")
            
            if len(backup_files) > keep_count:
                # Sort by modification time (newest first)
                backup_files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
                
                # Remove old files
                for old_file in backup_files[keep_count:]:
                    try:
                        os.remove(old_file)
                        print(f"🗑️  Removed old backup: {old_file}")
                    except Exception as e:
                        print(f"⚠️  Could not remove old backup {old_file}: {e}")
                        
        except Exception as e:
            print(f"⚠️  Could not cleanup old backups: {e}")
    
    def is_contract_cached(self, file_path: str) -> bool:
        """Check if a license contract has already been processed"""
        file_stats = os.path.getmtime(file_path)
        cached_data = self.processed_data_cache.get(file_path)
        
        if cached_data:
            # Check if file was modified since last processing
            cached_mtime = cached_data.get('mtime', 0)
            if file_stats <= cached_mtime:
                return True
        return False
    
    def get_cached_contract(self, file_path: str) -> Dict:
        """Get cached license contract data"""
        return self.processed_data_cache.get(file_path, {})
    
    def cache_contract_data(self, file_path: str, contract_data, metadata: Dict):
        """Cache processed license contract data with full structure"""
        
        # Convert the LicenseContract object to a dictionary with full structure
        contract_dict = self._contract_to_dict(contract_data)
        
        self.processed_data_cache[file_path] = {
            'contract': contract_dict,  # Full contract data structure
            'metadata': metadata,
            'processed_at': datetime.now().isoformat(),
            'mtime': os.path.getmtime(file_path)
        }
    
    def _contract_to_dict(self, contract_data) -> Dict:
        """Convert LicenseContract object to dictionary with full structure"""
        
        def serialize_date(date_obj):
            """Serialize date objects to string"""
            if date_obj:
                return str(date_obj)
            return None
        
        def serialize_enum(enum_obj):
            """Serialize enum objects to string"""
            if enum_obj:
                return enum_obj.value if hasattr(enum_obj, 'value') else str(enum_obj)
            return None
        
        def serialize_party(party):
            """Serialize Party object to dictionary"""
            if not party:
                return None
            return {
                'name': getattr(party, 'name', 'Unknown'),
                'address': getattr(party, 'address', None),
                'entity_type': getattr(party, 'entity_type', None),
                'jurisdiction': getattr(party, 'jurisdiction', None),
                'contact_info': getattr(party, 'contact_info', None)
            }
        
        def serialize_patents(patents):
            """Serialize list of LicensedPatent objects"""
            if not patents:
                return []
            return [
                {
                    'patent_number': getattr(patent, 'patent_number', ''),
                    'patent_title': getattr(patent, 'patent_title', None),
                    'filing_date': serialize_date(getattr(patent, 'filing_date', None)),
                    'issue_date': serialize_date(getattr(patent, 'issue_date', None))
                }
                for patent in patents
            ]
        
        def serialize_products(products):
            """Serialize list of LicensedProduct objects"""
            if not products:
                return []
            return [
                {
                    'product_name': getattr(product, 'product_name', ''),
                    'description': getattr(product, 'description', None),
                    'category': getattr(product, 'category', None)
                }
                for product in products
            ]
        
        def serialize_territories(territories):
            """Serialize list of LicensedTerritory objects"""
            if not territories:
                return []
            return [
                {
                    'territory_name': getattr(territory, 'territory_name', ''),
                    'territory_type': getattr(territory, 'territory_type', None),
                    'restrictions': getattr(territory, 'restrictions', None)
                }
                for territory in territories
            ]
        
        def serialize_milestones(milestones):
            """Serialize list of ExclusivityMilestone objects"""
            if not milestones:
                return []
            return [
                {
                    'description': getattr(milestone, 'description', ''),
                    'sales_target': getattr(milestone, 'sales_target', None),
                    'deadline': serialize_date(getattr(milestone, 'deadline', None)),
                    'consequences': getattr(milestone, 'consequences', None)
                }
                for milestone in milestones
            ]
        
        def serialize_sublicense_restrictions(restrictions):
            """Serialize list of SublicenseRestriction objects"""
            if not restrictions:
                return []
            return [
                {
                    'restriction_type': getattr(restriction, 'restriction_type', ''),
                    'description': getattr(restriction, 'description', ''),
                    'conditions': getattr(restriction, 'conditions', None)
                }
                for restriction in restrictions
            ]
        
        def serialize_diligence_clauses(clauses):
            """Serialize list of DiligenceClause objects"""
            if not clauses:
                return []
            return [
                {
                    'requirement_type': getattr(clause, 'requirement_type', ''),
                    'description': getattr(clause, 'description', ''),
                    'timeline': getattr(clause, 'timeline', None),
                    'consequences': getattr(clause, 'consequences', None)
                }
                for clause in clauses
            ]
        
        def serialize_exhibits(exhibits):
            """Serialize list of ExhibitAttachment objects"""
            if not exhibits:
                return []
            return [
                {
                    'name': getattr(exhibit, 'name', ''),
                    'type': getattr(exhibit, 'type', None),
                    'description': getattr(exhibit, 'description', None),
                    'reference_section': getattr(exhibit, 'reference_section', None)
                }
                for exhibit in exhibits
            ]
        
        # Build the complete contract dictionary
        contract_dict = {
            # Basic Contract Information
            'title': getattr(contract_data, 'title', 'Unknown'),
            'contract_type': getattr(contract_data, 'contract_type', 'License Agreement'),
            'summary': getattr(contract_data, 'summary', ''),
            
            # Key Dates
            'execution_date': serialize_date(getattr(contract_data, 'execution_date', None)),
            'effective_date': serialize_date(getattr(contract_data, 'effective_date', None)),
            'expiration_date': serialize_date(getattr(contract_data, 'expiration_date', None)),
            
            # Parties
            'licensor': serialize_party(getattr(contract_data, 'licensor', None)),
            'licensee': serialize_party(getattr(contract_data, 'licensee', None)),
            
            # Agreement Grants
            'agreement_grants': getattr(contract_data, 'agreement_grants', None),
            
            # Exclusivity
            'exclusivity_grant_type': serialize_enum(getattr(contract_data, 'exclusivity_grant_type', None)),
            'exclusivity_milestones': serialize_milestones(getattr(contract_data, 'exclusivity_milestones', [])),
            
            # Sublicensing
            'right_to_sublicense': getattr(contract_data, 'right_to_sublicense', None),
            'sublicense_restrictions': serialize_sublicense_restrictions(getattr(contract_data, 'sublicense_restrictions', [])),
            
            # Cross-licensing
            'crosslicensing_indicator': getattr(contract_data, 'crosslicensing_indicator', None),
            
            # Licensed Materials
            'licensed_field_of_use': getattr(contract_data, 'licensed_field_of_use', None),
            'licensed_patents': serialize_patents(getattr(contract_data, 'licensed_patents', [])),
            'licensed_products': serialize_products(getattr(contract_data, 'licensed_products', [])),
            'licensed_territory': serialize_territories(getattr(contract_data, 'licensed_territory', [])),
            
            # Contract Terms
            'contract_term': serialize_enum(getattr(contract_data, 'contract_term', None)),
            'contract_term_details': getattr(contract_data, 'contract_term_details', None),
            
            # Releases and Covenants
            'contract_releases': getattr(contract_data, 'contract_releases', None),
            'non_compete_covenant_indicator': getattr(contract_data, 'non_compete_covenant_indicator', None),
            
            # Rights
            'retained_licensor_rights': getattr(contract_data, 'retained_licensor_rights', None),
            'product_branding_rights': getattr(contract_data, 'product_branding_rights', None),
            
            # OEM Information
            'oem_type': serialize_enum(getattr(contract_data, 'oem_type', None)),
            
            # Use Restrictions
            'license_use_restrictions': getattr(contract_data, 'license_use_restrictions', None),
            
            # Obligations
            'licensor_obligations': getattr(contract_data, 'licensor_obligations', None),
            
            # Improvements
            'licensor_improvements_clause': getattr(contract_data, 'licensor_improvements_clause', None),
            'licensee_improvements_clause': getattr(contract_data, 'licensee_improvements_clause', None),
            'licensee_right_to_improvements': getattr(contract_data, 'licensee_right_to_improvements', None),
            
            # Related Parties
            'related_parties_licensor': getattr(contract_data, 'related_parties_licensor', None),
            'related_parties_licensee': getattr(contract_data, 'related_parties_licensee', None),
            'related_parties_unknown': getattr(contract_data, 'related_parties_unknown', None),
            
            # Financial Terms
            'upfront_payment': getattr(contract_data, 'upfront_payment', None),
            'stacking_clause_indicator': getattr(contract_data, 'stacking_clause_indicator', None),
            'stacking_clause_terms': getattr(contract_data, 'stacking_clause_terms', None),
            'most_favored_nations_clause': getattr(contract_data, 'most_favored_nations_clause', None),
            
            # Indemnities
            'licensee_infringement_indemnities': getattr(contract_data, 'licensee_infringement_indemnities', None),
            'licensor_product_liability_indemnities': getattr(contract_data, 'licensor_product_liability_indemnities', None),
            'licensee_product_liability_indemnities': getattr(contract_data, 'licensee_product_liability_indemnities', None),
            
            # Delivery and Supply
            'delivery_supply': getattr(contract_data, 'delivery_supply', None),
            
            # Relationship
            'relationship_between_contract_parties_clause': getattr(contract_data, 'relationship_between_contract_parties_clause', None),
            
            # Warranties
            'warranties_litigation': getattr(contract_data, 'warranties_litigation', None),
            'warranties_infringement': getattr(contract_data, 'warranties_infringement', None),
            'warranties_ip_sufficiency': getattr(contract_data, 'warranties_ip_sufficiency', None),
            'warranties_product_or_service': getattr(contract_data, 'warranties_product_or_service', None),
            
            # Assignment
            'assignment_restrictions': serialize_enum(getattr(contract_data, 'assignment_restrictions', None)),
            'assignment_restrictions_details': getattr(contract_data, 'assignment_restrictions_details', None),
            
            # Insurance and Audit
            'insurance_clause_indicator': getattr(contract_data, 'insurance_clause_indicator', None),
            'audit_clause': getattr(contract_data, 'audit_clause', None),
            
            # Delivery and Performance
            'late_delivery_clauses': getattr(contract_data, 'late_delivery_clauses', None),
            'diligence_clause': serialize_diligence_clauses(getattr(contract_data, 'diligence_clause', [])),
            
            # Confidentiality
            'confidential_agreement': getattr(contract_data, 'confidential_agreement', None),
            'confidential_materials': getattr(contract_data, 'confidential_materials', None),
            
            # Patent Management
            'patent_prosecution_responsibilities': getattr(contract_data, 'patent_prosecution_responsibilities', None),
            'suspected_infringement_clause': getattr(contract_data, 'suspected_infringement_clause', None),
            
            # Legal Representatives
            'legal_representative_organization': getattr(contract_data, 'legal_representative_organization', None),
            'legal_representative_lawyer': getattr(contract_data, 'legal_representative_lawyer', None),
            
            # Exhibits and Attachments
            'list_of_exhibits_and_attachments_in_contract': serialize_exhibits(getattr(contract_data, 'list_of_exhibits_and_attachments_in_contract', [])),
            
            # Additional Terms
            'governing_law': getattr(contract_data, 'governing_law', None),
            'jurisdiction': getattr(contract_data, 'jurisdiction', None),
            'termination_rights': getattr(contract_data, 'termination_rights', None),
            'dispute_resolution': getattr(contract_data, 'dispute_resolution', None),
            
            # Risk Factors and Disclosures
            'risk_factors': getattr(contract_data, 'risk_factors', []),
            'material_changes': getattr(contract_data, 'material_changes', None),
            
            # Regulatory Compliance
            'regulatory_requirements': getattr(contract_data, 'regulatory_requirements', None),
            'export_control': getattr(contract_data, 'export_control', None)
        }
        
        return contract_dict
    
    def _extract_year(self, file_path: str) -> int:
        """Extract year from file path for sorting"""
        try:
            parts = file_path.split('/')
            for part in parts:
                if part.isdigit() and len(part) == 4:
                    return int(part)
        except:
            pass
        return 0
    
    def _extract_file_metadata(self, file_path: str) -> Dict[str, str]:
        """Extract metadata from file path"""
        parts = file_path.split('/')
        
        metadata = {
            'file_path': file_path,
            'year': 'Unknown',
            'filing_type': 'Unknown',
            'accession': 'Unknown',
            'exhibit': 'Unknown'
        }
        
        try:
            # Extract year (e.g., 2022)
            for part in parts:
                if part.isdigit() and len(part) == 4:
                    metadata['year'] = part
                    break
            
            # Extract filing type and accession from path
            for i, part in enumerate(parts):
                if 'license' in part.lower() or 'agreement' in part.lower():
                    metadata['filing_type'] = part
                if len(part) > 10 and part.isalnum():  # Potential accession number
                    metadata['accession'] = part
                if 'exhibit' in part.lower() or 'schedule' in part.lower():
                    metadata['exhibit'] = part
        except:
            pass
        
        return metadata
    
    def process_single_contract(self, file_path: str, file_type: str, index: int, total: int) -> bool:
        """Process a single license contract file"""
        
        if not self.pipeline:
            print(f"❌ Pipeline not initialized, skipping {file_path}")
            return False
        
        print(f"\n📄 Processing {index}/{total}: {os.path.basename(file_path)}")
        
        # Check cache first
        if self.is_contract_cached(file_path):
            cached_data = self.get_cached_contract(file_path)
            print(f"✅ Using cached data for {os.path.basename(file_path)}")
            
            # Display cached contract information
            if 'contract' in cached_data:
                contract = cached_data['contract']
                print(f"   Cached title: {contract.get('title', 'Unknown')}")
                print(f"   Cached type: {contract.get('contract_type', 'Unknown')}")
                
                # Show licensor and licensee info
                licensor = contract.get('licensor', {})
                licensee = contract.get('licensee', {})
                print(f"   Licensor: {licensor.get('name', 'Unknown')} ({licensor.get('entity_type', 'Unknown')})")
                print(f"   Licensee: {licensee.get('name', 'Unknown')} ({licensee.get('entity_type', 'Unknown')})")
                
                # Show key details
                print(f"   Exclusivity: {contract.get('exclusivity_grant_type', 'Unknown')}")
                print(f"   Upfront Payment: ${contract.get('upfront_payment', 0):,.2f}" if contract.get('upfront_payment') else "   Upfront Payment: Not specified")
                print(f"   Patents: {len(contract.get('licensed_patents', []))}")
                print(f"   Products: {len(contract.get('licensed_products', []))}")
                print(f"   Territories: {len(contract.get('licensed_territory', []))}")
            else:
                # Handle old cache format for backward compatibility
                print(f"   Cached title: {cached_data.get('title', 'Unknown')}")
                print(f"   Cached type: {cached_data.get('contract_type', 'Unknown')}")
            
            return True
        
        try:
            # Extract text based on file type
            if file_type.lower() in ['html', 'htm']:
                contract_text = extract_text_from_html(file_path)
            elif file_type.lower() == 'txt':
                contract_text = extract_text_from_txt(file_path)
            elif file_type.lower() == 'pdf':
                # For PDF files, you might need additional processing
                print(f"⚠️  PDF processing not implemented yet, skipping {file_path}")
                return False
            else:
                print(f"⚠️  Unsupported file type: {file_type}")
                return False
            
            if not contract_text or len(contract_text.strip()) < 100:
                print(f"⚠️  File appears to be empty or too short: {file_path}")
                return False
            
            # Extract metadata
            metadata = self._extract_file_metadata(file_path)
            
            # Process with pipeline
            print(f"🔧 Extracting license contract data...")
            contract_data = self.pipeline.ingest_contract(contract_text, contract_id=metadata.get('accession'))
            
            # Cache the processed data
            self.cache_contract_data(file_path, contract_data, metadata)
            
            # Print summary with rich information
            print(f"✅ Successfully processed: {contract_data.title}")
            print(f"   Type: {contract_data.contract_type}")
            
            # Show detailed party information
            if contract_data.licensor:
                print(f"   Licensor: {contract_data.licensor.name}")
                if contract_data.licensor.entity_type:
                    print(f"     Entity Type: {contract_data.licensor.entity_type}")
                if contract_data.licensor.jurisdiction:
                    print(f"     Jurisdiction: {contract_data.licensor.jurisdiction}")
            
            if contract_data.licensee:
                print(f"   Licensee: {contract_data.licensee.name}")
                if contract_data.licensee.entity_type:
                    print(f"     Entity Type: {contract_data.licensee.entity_type}")
                if contract_data.licensee.jurisdiction:
                    print(f"     Jurisdiction: {contract_data.licensee.jurisdiction}")
            
            # Show key contract details
            print(f"   Exclusivity: {contract_data.exclusivity_grant_type.value if contract_data.exclusivity_grant_type else 'Unknown'}")
            print(f"   Upfront Payment: ${contract_data.upfront_payment:,.2f}" if contract_data.upfront_payment else "   Upfront Payment: Not specified")
            
            # Show licensed materials
            print(f"   Patents: {len(contract_data.licensed_patents)}")
            for patent in contract_data.licensed_patents[:3]:  # Show first 3
                print(f"     - {patent.patent_number}: {patent.patent_title or 'No title'}")
            if len(contract_data.licensed_patents) > 3:
                print(f"     ... and {len(contract_data.licensed_patents) - 3} more")
            
            print(f"   Products: {len(contract_data.licensed_products)}")
            for product in contract_data.licensed_products[:3]:  # Show first 3
                print(f"     - {product.product_name}: {product.description or 'No description'}")
            if len(contract_data.licensed_products) > 3:
                print(f"     ... and {len(contract_data.licensed_products) - 3} more")
            
            print(f"   Territories: {len(contract_data.licensed_territory)}")
            for territory in contract_data.licensed_territory[:3]:  # Show first 3
                print(f"     - {territory.territory_name} ({territory.territory_type or 'Unknown type'})")
            if len(contract_data.licensed_territory) > 3:
                print(f"     ... and {len(contract_data.licensed_territory) - 3} more")
            
            # Show additional key information
            if contract_data.governing_law:
                print(f"   Governing Law: {contract_data.governing_law}")
            if contract_data.jurisdiction:
                print(f"   Jurisdiction: {contract_data.jurisdiction}")
            if contract_data.licensed_field_of_use:
                print(f"   Field of Use: {contract_data.licensed_field_of_use}")
            
            self.processed_files.append(file_path)
            return True
            
        except Exception as e:
            print(f"❌ Error processing {file_path}: {e}")
            self.failed_files.append((file_path, str(e)))
            return False
    
    def run_batch_processing(self, max_contracts: int = None, force_reprocess: bool = False) -> Dict:
        """Run batch processing of all license contracts"""
        
        if not self.pipeline:
            print("❌ Pipeline not initialized. Cannot process contracts.")
            return {"error": "Pipeline not initialized"}
        
        print("🚀 Starting license contract batch processing...")
        self.start_time = time.time()
        
        # Load cache
        self.load_processed_cache()
        
        # Find all contract files
        contract_files = self.find_all_contract_files()
        
        if not contract_files:
            print("❌ No license contract files found!")
            return {"error": "No contract files found"}
        
        print(f"📋 Found {len(contract_files)} license contract files to process")
        
        # Limit processing if specified
        if max_contracts:
            contract_files = contract_files[:max_contracts]
            print(f"📊 Limiting processing to {max_contracts} contracts")
        
        # Process each contract
        successful_count = 0
        total_files = len(contract_files)
        
        for index, (file_path, file_type) in enumerate(contract_files, 1):
            try:
                if self.process_single_contract(file_path, file_type, index, total_files):
                    successful_count += 1
                
                # Save cache periodically
                if index % 10 == 0:
                    self.save_processed_cache()
                    print(f"💾 Progress: {index}/{total_files} contracts processed")
                
                # Small delay to avoid overwhelming the system
                time.sleep(0.1)
                
            except KeyboardInterrupt:
                print("\n⚠️  Processing interrupted by user")
                break
            except Exception as e:
                print(f"❌ Unexpected error processing {file_path}: {e}")
                self.failed_files.append((file_path, str(e)))
        
        # Final cache save
        self.save_processed_cache()
        
        # Generate final report
        report = self._generate_final_report(total_files, successful_count)
        
        print(f"\n🎉 License contract batch processing completed!")
        print(f"   Total files: {total_files}")
        print(f"   Successful: {successful_count}")
        print(f"   Failed: {len(self.failed_files)}")
        print(f"   Success rate: {(successful_count/total_files)*100:.1f}%")
        
        return report
    
    def _generate_final_report(self, total_files: int, successful_count: int) -> Dict:
        """Generate a comprehensive final report"""
        
        processing_time = time.time() - self.start_time if self.start_time else 0
        
        report = {
            "processing_summary": {
                "total_files": total_files,
                "successful_count": successful_count,
                "failed_count": len(self.failed_files),
                "success_rate": (successful_count/total_files)*100 if total_files > 0 else 0,
                "processing_time_seconds": processing_time,
                "processing_time_minutes": processing_time / 60,
                "files_per_minute": (successful_count / (processing_time / 60)) if processing_time > 0 else 0
            },
            "failed_files": [
                {
                    "file_path": file_path,
                    "error": error
                }
                for file_path, error in self.failed_files
            ],
            "cache_stats": {
                "cached_contracts": len(self.processed_data_cache),
                "cache_file": self.cache_file
            },
            "timestamp": datetime.now().isoformat()
        }
        
        return report
    
    def run_interactive_query_session(self):
        """Run an interactive query session for license contracts"""
        
        if not self.pipeline:
            print("❌ Pipeline not initialized. Cannot run queries.")
            return
        
        print("\n🔍 Starting interactive license contract query session...")
        print("Type 'quit' to exit, 'stats' for database statistics")
        
        while True:
            try:
                query = input("\n❓ Enter your question about license contracts: ").strip()
                
                if query.lower() in ['quit', 'exit', 'q']:
                    print("👋 Goodbye!")
                    break
                
                if query.lower() == 'stats':
                    stats = self.pipeline.get_database_stats()
                    print(f"\n📊 Database Statistics:")
                    for key, value in stats.items():
                        print(f"   {key}: {value}")
                    continue
                
                if not query:
                    continue
                
                print(f"🔍 Searching for: {query}")
                response = self.pipeline.query_contracts(query)
                print(f"\n💡 Answer: {response}")
                
            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"❌ Error: {e}")
    
    def cleanup(self):
        """Clean up resources"""
        if self.pipeline:
            self.pipeline.close()

def main():
    """Main function to run license contract batch processing"""
    
    processor = EnhancedLicenseBatchProcessor()
    
    try:
        # Run batch processing
        report = processor.run_batch_processing(max_contracts=None)  # Process all contracts
        
        if "error" not in report:
            print("\n📊 Final Report:")
            print(json.dumps(report, indent=2))
            
            # Offer interactive query session
            response = input("\n🔍 Would you like to run an interactive query session? (y/n): ")
            if response.lower() in ['y', 'yes']:
                processor.run_interactive_query_session()
        
    except KeyboardInterrupt:
        print("\n⚠️  Processing interrupted by user")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        processor.cleanup()

if __name__ == "__main__":
    main() 