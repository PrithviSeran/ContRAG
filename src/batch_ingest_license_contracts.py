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
            self.pipeline = LicenseGraphRAGPipeline()
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
    
    def load_processed_cache(self) -> bool:
        """Load previously processed license contract data from cache"""
        try:
            if os.path.exists(self.cache_file):
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    self.processed_data_cache = json.load(f)
                print(f"📁 Loaded cache with {len(self.processed_data_cache)} previously processed license contracts")
                return True
        except Exception as e:
            print(f"⚠️ Warning: Could not load cache: {e}")
        return False
    
    def save_processed_cache(self):
        """Save processed license contract data to cache"""
        try:
            # Save main cache file
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(self.processed_data_cache, f, indent=2, default=str)
            
            # Create backup with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = f"processed_license_contracts_cache_backup_{timestamp}.json"
            with open(backup_file, 'w', encoding='utf-8') as f:
                json.dump(self.processed_data_cache, f, indent=2, default=str)
            
            print(f"💾 Saved cache with {len(self.processed_data_cache)} processed license contracts")
            print(f"💾 Backup saved: {backup_file}")
        except Exception as e:
            print(f"⚠️ Warning: Could not save cache: {e}")
    
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
        """Cache processed license contract data"""
        self.processed_data_cache[file_path] = {
            'contract_id': getattr(contract_data, 'title', 'Unknown'),
            'title': getattr(contract_data, 'title', 'Unknown'),
            'contract_type': getattr(contract_data, 'contract_type', 'Unknown'),
            'summary': getattr(contract_data, 'summary', ''),
            'execution_date': str(getattr(contract_data, 'execution_date', '')),
            'effective_date': str(getattr(contract_data, 'effective_date', '')),
            'upfront_payment': getattr(contract_data, 'upfront_payment', None),
            'exclusivity_grant_type': getattr(contract_data, 'exclusivity_grant_type', None),
            'oem_type': getattr(contract_data, 'oem_type', None),
            'licensor_name': getattr(contract_data.licensor, 'name', 'Unknown') if contract_data.licensor else 'Unknown',
            'licensee_name': getattr(contract_data.licensee, 'name', 'Unknown') if contract_data.licensee else 'Unknown',
            'patents_count': len(getattr(contract_data, 'licensed_patents', [])),
            'products_count': len(getattr(contract_data, 'licensed_products', [])),
            'territories_count': len(getattr(contract_data, 'licensed_territory', [])),
            'metadata': metadata,
            'processed_at': datetime.now().isoformat(),
            'mtime': os.path.getmtime(file_path)
        }
    
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
            
            # Print summary
            print(f"✅ Successfully processed: {contract_data.title}")
            print(f"   Type: {contract_data.contract_type}")
            print(f"   Licensor: {contract_data.licensor.name if contract_data.licensor else 'Unknown'}")
            print(f"   Licensee: {contract_data.licensee.name if contract_data.licensee else 'Unknown'}")
            print(f"   Exclusivity: {contract_data.exclusivity_grant_type.value if contract_data.exclusivity_grant_type else 'Unknown'}")
            print(f"   Upfront Payment: ${contract_data.upfront_payment:,.2f}" if contract_data.upfront_payment else "   Upfront Payment: Not specified")
            print(f"   Patents: {len(contract_data.licensed_patents)}")
            print(f"   Products: {len(contract_data.licensed_products)}")
            print(f"   Territories: {len(contract_data.licensed_territory)}")
            
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