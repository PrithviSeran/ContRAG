#!/usr/bin/env python3
"""
Enhanced Batch ingest for all securities contracts from ABEONA-THERAPEUTICS-INC folder
Optimized for processing all 61 contract files effectively
"""

import os
import glob
import time
import json
from datetime import datetime
from typing import List, Dict, Tuple
from .securities_pipeline_runner import SecuritiesGraphRAGPipeline, extract_text_from_html, extract_text_from_txt

class EnhancedBatchProcessor:
    """Enhanced batch processor for all ABEONA contracts"""
    
    def __init__(self):
        self.pipeline = None
        self.processed_files = []
        self.failed_files = []
        self.start_time = None
        self.processed_data_cache = {}  # Cache for processed contract data
        self.cache_file = "processed_contracts_cache.json"
        
        # Initialize pipeline immediately to avoid None errors
        try:
            print("🔧 Attempting to initialize pipeline...")
            self.pipeline = SecuritiesGraphRAGPipeline()
            print("✅ Pipeline initialized in constructor")
        except Exception as e:
            print(f"❌ Error: Could not initialize pipeline in constructor: {e}")
            print(f"   Error type: {type(e).__name__}")
            import traceback
            print(f"   Traceback: {traceback.format_exc()}")
            self.pipeline = None
        
    def find_all_contract_files(self, base_dir=None) -> List[Tuple[str, str]]:
        """Find all contract files with their types"""
        
        if base_dir is None:
            base_dir = os.getenv("ABEONA_DATA_PATH", "data/ABEONA-THERAPEUTICS-INC")
        
        print(f"🔍 Searching for contract files in: {os.path.abspath(base_dir)}")
        
        contract_files = []
        
        # Check if this is the uploads directory (for frontend uploads)
        is_upload_dir = "uploads" in base_dir
        
        if is_upload_dir:
            # For uploads directory, search non-recursively to avoid duplicates
            print("📁 Detected uploads directory - searching non-recursively")
            for extension in ["*.html", "*.htm", "*.txt"]:
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
        
        print(f"📋 Found {len(unique_files)} unique contract files")
        
        # Sort by year and type for logical processing order
        unique_files.sort(key=lambda x: (self._extract_year(x[0]), x[1]))
        
        return unique_files
    
    def load_processed_cache(self) -> bool:
        """Load previously processed contract data from cache"""
        try:
            if os.path.exists(self.cache_file):
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    self.processed_data_cache = json.load(f)
                print(f"📁 Loaded cache with {len(self.processed_data_cache)} previously processed contracts")
                return True
        except Exception as e:
            print(f"⚠️ Warning: Could not load cache: {e}")
        return False
    
    def save_processed_cache(self):
        """Save processed contract data to cache"""
        try:
            # Save main cache file
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(self.processed_data_cache, f, indent=2, default=str)
            
            # Create backup with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = f"processed_contracts_cache_backup_{timestamp}.json"
            with open(backup_file, 'w', encoding='utf-8') as f:
                json.dump(self.processed_data_cache, f, indent=2, default=str)
            
            print(f"💾 Saved cache with {len(self.processed_data_cache)} processed contracts")
            print(f"💾 Backup saved: {backup_file}")
        except Exception as e:
            print(f"⚠️ Warning: Could not save cache: {e}")
    
    def is_contract_cached(self, file_path: str) -> bool:
        """Check if a contract has already been processed"""
        file_stats = os.path.getmtime(file_path)
        cached_data = self.processed_data_cache.get(file_path)
        
        if cached_data:
            # Check if file was modified since last processing
            cached_mtime = cached_data.get('mtime', 0)
            if file_stats <= cached_mtime:
                return True
        return False
    
    def get_cached_contract(self, file_path: str) -> Dict:
        """Get cached contract data"""
        return self.processed_data_cache.get(file_path, {})
    
    def cache_contract_data(self, file_path: str, contract_data, metadata: Dict):
        """Cache processed contract data"""
        self.processed_data_cache[file_path] = {
            'contract_id': getattr(contract_data, 'title', 'Unknown'),
            'title': getattr(contract_data, 'title', 'Unknown'),
            'contract_type': getattr(contract_data, 'contract_type', 'Unknown'),
            'summary': getattr(contract_data, 'summary', ''),
            'execution_date': str(getattr(contract_data, 'execution_date', '')),
            'total_offering_amount': getattr(contract_data, 'total_offering_amount', None),
            'parties_count': len(getattr(contract_data, 'parties', [])),
            'securities_count': len(getattr(contract_data, 'securities', [])),
            'conditions_count': len(getattr(contract_data, 'closing_conditions', [])),
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
            
            # Extract filing type (e.g., 10-K, 10-Q, 8-K)
            for part in parts:
                if any(filing in part for filing in ['10-K', '10-Q', '8-K', 'S-1']):
                    metadata['filing_type'] = part
                    break
            
            # Extract accession number (e.g., 0001493152-22-021969)
            for part in parts:
                if '-' in part and len(part) > 10:
                    metadata['accession'] = part
                    break
            
            # Extract exhibit number from filename
            filename = os.path.basename(file_path)
            if filename.startswith('10.') or filename.startswith('EX-10.'):
                metadata['exhibit'] = filename.replace('.html', '').replace('.txt', '')
        
        except Exception as e:
            print(f"Warning: Could not extract metadata from {file_path}: {e}")
        
        return metadata
    
    def process_single_contract(self, file_path: str, file_type: str, index: int, total: int) -> bool:
        """Process a single contract file"""
        
        print(f"\n{'='*80}")
        print(f"PROCESSING CONTRACT {index}/{total}")
        print(f"File: {file_path}")
        print(f"Type: {file_type.upper()}")
        
        # Check if already processed and cached (unless force reprocessing)
        if not getattr(self, '_force_reprocess', False) and self.is_contract_cached(file_path):
            cached_data = self.get_cached_contract(file_path)
            print("🏃‍♂️ USING CACHED DATA (skipping LLM call)")
            print(f"✅ Cached: {cached_data.get('title', 'Unknown')}")
            print(f"📊 Type: {cached_data.get('contract_type', 'Unknown')}")
            print(f"⏰ Processed: {cached_data.get('processed_at', 'Unknown')}")
            
            # Add to processed files list
            self.processed_files.append({
                'file_path': file_path,
                'contract_id': cached_data.get('contract_id', 'Unknown'),
                'title': cached_data.get('title', 'Unknown'),
                'type': cached_data.get('contract_type', 'Unknown'),
                'metadata': cached_data.get('metadata', {}),
                'from_cache': True
            })
            return True
        
        print("="*80)
        
        try:
            # Extract metadata
            metadata = self._extract_file_metadata(file_path)
            print(f"📅 Year: {metadata['year']}")
            print(f"📄 Filing Type: {metadata['filing_type']}")
            print(f"🔢 Accession: {metadata['accession']}")
            print(f"📋 Exhibit: {metadata['exhibit']}")
            
            # Extract text based on file type
            if file_type in ['html', 'htm']:
                contract_text = extract_text_from_html(file_path)
            else:  # txt
                contract_text = extract_text_from_txt(file_path)
            
            if not contract_text or len(contract_text.strip()) < 100:
                print("❌ Error: Insufficient contract text extracted")
                return False
            
            print(f"📝 Extracted {len(contract_text)} characters")
            
            # Truncate very long contracts for efficiency while preserving key information
            if len(contract_text) > 20000:
                # Take first 15000 chars and last 5000 chars to capture beginning and end
                contract_text = contract_text[:15000] + "\n...[MIDDLE CONTENT TRUNCATED]...\n" + contract_text[-5000:]
                print(f"📝 Truncated to {len(contract_text)} characters for processing")
            
            # Create meaningful contract ID
            contract_id = f"{metadata['year']}-{metadata['exhibit']}-{metadata['accession'][:10]}"
            
            # Ensure pipeline is initialized
            if self.pipeline is None:
                print("🔧 Pipeline not initialized, attempting to initialize now...")
                try:
                    self.pipeline = SecuritiesGraphRAGPipeline()
                    print("✅ Pipeline initialized successfully")
                except Exception as init_error:
                    print(f"❌ Failed to initialize pipeline: {init_error}")
                    print(f"   Error type: {type(init_error).__name__}")
                    import traceback
                    print(f"   Traceback: {traceback.format_exc()}")
                    print("💡 Possible issues:")
                    print("   - Missing environment variables (GOOGLE_API_KEY, NEO4J_URI, etc.)")
                    print("   - Neo4j database not running")
                    print("   - Missing dependencies")
                    return False
            
            # Process with pipeline (this uses LLM)
            print("🤖 Processing with AI extraction...")
            contract_data = self.pipeline.ingest_contract(contract_text, contract_id)
            
            print(f"✅ Successfully processed: {contract_data.title}")
            print(f"📊 Contract Type: {contract_data.contract_type}")
            print(f"💰 Total Amount: {getattr(contract_data, 'total_offering_amount', 'N/A')}")
            print(f"👥 Parties: {len(getattr(contract_data, 'parties', []))}")
            print(f"📜 Securities: {len(getattr(contract_data, 'securities', []))}")
            print(f"✓ Conditions: {len(getattr(contract_data, 'closing_conditions', []))}")
            
            # Cache the processed data
            self.cache_contract_data(file_path, contract_data, metadata)
            
            # Track success
            self.processed_files.append({
                'file_path': file_path,
                'contract_id': contract_id,
                'title': contract_data.title,
                'type': contract_data.contract_type,
                'metadata': metadata,
                'from_cache': False
            })
            
            # Save cache periodically (every 5 contracts)
            if len(self.processed_files) % 5 == 0:
                self.save_processed_cache()
            
            return True
            
        except Exception as e:
            print(f"❌ Error processing {file_path}: {e}")
            self.failed_files.append({
                'file_path': file_path,
                'error': str(e),
                'metadata': metadata if 'metadata' in locals() else {}
            })
            return False
    
    def run_batch_processing(self, max_contracts: int = None, force_reprocess: bool = False) -> Dict:
        """Run the complete batch processing pipeline"""
        
        self.start_time = time.time()
        print("🚀 STARTING ENHANCED BATCH CONTRACT INGESTION")
        print("="*80)
        
        # Set force reprocess flag for the instance
        self._force_reprocess = force_reprocess
        
        # Load existing cache (unless force reprocessing)
        if force_reprocess:
            print("🔄 Force reprocessing enabled - ignoring cache")
            self.processed_data_cache = {}
        else:
            print("📁 Loading processed contracts cache...")
            self.load_processed_cache()
        
        # Find all contract files
        print("🔍 Discovering contract files...")
        contract_files = self.find_all_contract_files()
        
        if not contract_files:
            return {"error": "No contract files found"}
        
        print(f"✅ Found {len(contract_files)} contract files")
        
        # Count cached vs new files
        if force_reprocess:
            cached_count = 0
            new_count = len(contract_files)
            print(f"🤖 {new_count} files will be reprocessed with LLM")
        else:
            cached_count = sum(1 for file_path, _ in contract_files if self.is_contract_cached(file_path))
            new_count = len(contract_files) - cached_count
            print(f"🏃‍♂️ {cached_count} already processed (will use cache)")
            print(f"🤖 {new_count} new files (will use LLM processing)")
        
        # Group by type for reporting
        file_types = {}
        for file_path, file_type in contract_files:
            file_types[file_type] = file_types.get(file_type, 0) + 1
        
        print("📊 File Distribution:")
        for ftype, count in file_types.items():
            print(f"   {ftype.upper()}: {count} files")
        
        # Limit files if requested
        if max_contracts and len(contract_files) > max_contracts:
            contract_files = contract_files[:max_contracts]
            print(f"📝 Limited to first {max_contracts} contracts for this run")
        
        # Initialize pipeline
        print("\n🔧 Initializing GraphRAG pipeline...")
        try:
            self.pipeline = SecuritiesGraphRAGPipeline()
            print("✅ Pipeline initialized successfully")
        except Exception as e:
            return {"error": f"Pipeline initialization failed: {e}"}
        
        # Process each contract
        print(f"\n📋 Processing {len(contract_files)} contracts...")
        successful_count = 0
        
        for i, (file_path, file_type) in enumerate(contract_files, 1):
            if self.process_single_contract(file_path, file_type, i, len(contract_files)):
                successful_count += 1
            
            # Progress update every 5 files
            if i % 5 == 0:
                if self.start_time is not None:
                    elapsed = time.time() - self.start_time
                    rate = i / elapsed * 60  # files per minute
                    print(f"\n📈 Progress: {i}/{len(contract_files)} files processed")
                    print(f"⏱️  Rate: {rate:.1f} files/minute")
                    print(f"✅ Success rate: {successful_count/i*100:.1f}%")
                else:
                    print(f"\n📈 Progress: {i}/{len(contract_files)} files processed")
                    print(f"✅ Success rate: {successful_count/i*100:.1f}%")
        
        # Final results
        print(f"\n✅ Contract processing loop completed!")
        print(f"📊 Processed {len(contract_files)} files, {successful_count} successful")
        
        # Save final cache
        print("💾 Saving processed contracts cache...")
        self.save_processed_cache()
        
        print("🔄 Generating final report...")
        
        try:
            report = self._generate_final_report(len(contract_files), successful_count)
            print("✅ Final report generated successfully")
            return report
        except Exception as e:
            print(f"❌ Error generating final report: {e}")
            return {"error": f"Failed to generate final report: {e}"}
    
    def _generate_final_report(self, total_files: int, successful_count: int) -> Dict:
        """Generate comprehensive final report"""
        
        # Handle case where start_time was never set (API direct calls)
        if self.start_time is None:
            elapsed_time = 0  # Default when timing wasn't tracked
        else:
            elapsed_time = time.time() - self.start_time
        
        # Get database statistics with timeout protection
        print("\n📊 Retrieving database statistics...")
        try:
            # Add a simple timeout mechanism
            import signal
            def timeout_handler(signum, frame):
                raise TimeoutError("Database stats query timed out")
            
            signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(30)  # 30 second timeout
            
            db_stats = self.pipeline.get_database_stats()
            signal.alarm(0)  # Cancel the alarm
            print("✅ Database statistics retrieved successfully")
            
        except TimeoutError:
            print("⚠️  Database stats query timed out - using basic stats")
            db_stats = {"error": "Stats query timed out after 30 seconds"}
        except Exception as e:
            print(f"⚠️  Could not retrieve database stats: {e}")
            db_stats = {"error": f"Could not retrieve stats: {e}"}
        
        # Calculate rate safely
        rate = f"{total_files/elapsed_time*60:.1f} files/minute" if elapsed_time > 0 else "N/A"
        
        report = {
            "summary": {
                "total_files_found": total_files,
                "successfully_processed": successful_count,
                "failed_files": len(self.failed_files),
                "success_rate": f"{successful_count/total_files*100:.1f}%",
                "processing_time": f"{elapsed_time:.1f} seconds",
                "rate": rate
            },
            "database_stats": db_stats,
            "processed_files": self.processed_files,
            "failed_files": self.failed_files[:5]  # Show first 5 failures
        }
        
        print(f"\n🎉 BATCH PROCESSING COMPLETE!")
        print("="*80)
        print(f"📊 Final Results:")
        print(f"   Total Files: {total_files}")
        print(f"   Successfully Processed: {successful_count}")
        print(f"   Failed: {len(self.failed_files)}")
        print(f"   Success Rate: {successful_count/total_files*100:.1f}%")
        print(f"   Processing Time: {elapsed_time:.1f} seconds")
        print(f"   Rate: {rate}")
        
        print(f"\n📈 Database Statistics:")
        if "error" in db_stats:
            print(f"   ⚠️  {db_stats['error']}")
        else:
            for key, value in db_stats.items():
                print(f"   {key}: {value}")
        
        if self.failed_files:
            print(f"\n❌ Failed Files (first 5):")
            for failure in self.failed_files[:5]:
                print(f"   {failure['file_path']}: {failure['error'][:100]}...")
        
        return report
    
    def run_interactive_query_session(self):
        """Enhanced interactive querying session"""
        
        if not self.pipeline:
            print("❌ No pipeline available. Run batch processing first.")
            return
        
        print(f"\n{'='*80}")
        print("ENHANCED INTERACTIVE QUERY SESSION")
        print("="*80)
        print("Ask questions about Abeona Therapeutics contracts. Examples:")
        print("- 'What are all the securities purchase agreements?'")
        print("- 'Show me contracts from 2022'")
        print("- 'What types of securities were issued over the years?'")
        print("- 'Who are the key parties across all contracts?'")
        print("- 'What are the license agreements about?'")
        print("- 'Compare offering amounts across different years'")
        print("Type 'stats' for database statistics, 'quit' to exit.")
        print("")
        
        while True:
            try:
                query = input("🔍 Enter your question: ").strip()
                
                if query.lower() in ['quit', 'exit', 'q']:
                    break
                elif query.lower() == 'stats':
                    stats = self.pipeline.get_database_stats()
                    print("📊 Current Database Statistics:")
                    for key, value in stats.items():
                        print(f"   {key}: {value}")
                    continue
                
                if not query:
                    continue
                
                print(f"\n🤖 Processing: {query}")
                result = self.pipeline.query_contracts(query)
                print(f"📊 Answer:\n{result}")
                print("-" * 60)
                
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"❌ Error: {e}")
    
    def cleanup(self):
        """Clean up resources"""
        if self.pipeline:
            self.pipeline.close()
            print("\n👋 Pipeline closed. Database connection ended.")

def main():
    """Main execution function"""
    
    processor = EnhancedBatchProcessor()
    
    try:
        # Run batch processing (process all files by default)
        # Set max_contracts=10 for testing, None for all files
        report = processor.run_batch_processing(max_contracts=None)
        
        # Save report
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = f"batch_processing_report_{timestamp}.json"
        
        import json
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        print(f"\n📄 Detailed report saved to: {report_file}")
        
        # Interactive session
        if report.get("summary", {}).get("successfully_processed", 0) > 0:
            processor.run_interactive_query_session()
        
    except KeyboardInterrupt:
        print("\n⏹️  Processing interrupted by user")
    except Exception as e:
        print(f"\n❌ Critical error: {e}")
    finally:
        processor.cleanup()

if __name__ == "__main__":
    main() 