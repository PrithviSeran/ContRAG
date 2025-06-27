# 📜 GraphRAG for Securities Contracts

A sophisticated **Graph Retrieval-Augmented Generation (GraphRAG)** system for analyzing securities purchase agreements, license agreements, and other financial contracts. This system extracts structured data from legal documents and enables intelligent querying through a conversational AI interface.

**Currently processing:** 61 Abeona Therapeutics Inc. contracts (1996-2023)

## 🏗️ **Architecture Overview**

```
Contract Files (HTML/TXT) → [Enhanced AI + Rule-Based Extraction] → Structured Data → [Neo4j Import] → Knowledge Graph
                                                                                                            ↓
User Query → [AI Agent] → [Securities Contract Tool] → [Cypher Queries] → Intelligent Results
```

## 🚀 **Quick Start**

### **Prerequisites**

- Python 3.9+
- Docker & Docker Compose
- Google AI API Key (for Gemini)

### **1. Clone and Setup**

```bash
# Install dependencies
pip install -r requirements.txt

# Copy environment template
cp .env.example .env
```

### **2. Configure Environment**

Edit `.env` file:

```bash
# Get your API key from: https://makersuite.google.com/app/apikey
GOOGLE_API_KEY=your_google_ai_api_key_here

# Neo4j settings (default values work with Docker setup)
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=graphrag_password
```

### **3. Start Neo4j Database**

```bash
# Using Docker Compose (recommended)
cd config && docker-compose up -d

# Or using Docker directly
docker run -d \
  --name graphrag-neo4j \
  -p 7474:7474 -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/graphrag_password \
  neo4j:latest
```

### **4. Run the Enhanced Pipeline**

```bash
# Process all 61 Abeona Therapeutics contracts
python pipeline.py
```

## 📊 **What You'll See**

The enhanced pipeline will:

1. **Load Cache** - Skip previously processed contracts (saves LLM calls!)
2. **Smart Processing** - Use hybrid AI + rule-based extraction 
3. **Import to Graph** - Build comprehensive knowledge graph
4. **Interactive Queries** - Natural language contract analysis

**Example Output:**

```
🚀 STARTING ENHANCED BATCH CONTRACT INGESTION
================================================================

📁 Loading processed contracts cache...
💾 Loaded cache with 45 previously processed contracts

🔍 Discovering contract files...
✅ Found 61 contract files

🏃‍♂️ 45 already processed (will use cache)
🤖 16 new files (will use LLM processing)

📊 File Distribution:
   HTML: 24 files
   TXT: 37 files

================================================================
PROCESSING CONTRACT 46/61
File: data/ABEONA-THERAPEUTICS-INC/2022/10-Q/0001493152-22-021969/10.3.html
Type: HTML
================================================================

📅 Year: 2022
📄 Filing Type: 10-Q
🔢 Accession: 0001493152-22-021969
📋 Exhibit: 10.3.html

🤖 Processing with AI extraction...
✅ Successfully processed: License Agreement between Abeona and REGENXBIO
📊 Contract Type: License Agreement
💰 Total Amount: 5000000.0
👥 Parties: 2
📜 Securities: 0
✓ Conditions: 8

================================================================
FINAL RESULTS
================================================================
📊 Processed: 61/61 files
✅ Success Rate: 100%
📈 Database: 757 nodes, 761 relationships
⏱️  Processing Time: 125.3 seconds
```

## 🔧 **System Components**

### **Core Modules**

| File | Purpose |
|------|---------|
| `src/securities_data_models.py` | Pydantic schemas for securities contracts |
| `src/securities_extraction.py` | Enhanced AI + rule-based extraction |
| `src/securities_pipeline_runner.py` | Pipeline orchestration |
| `src/batch_ingest_contracts.py` | Batch processing with caching |
| `src/neo4j_persistence.py` | Graph database operations |

### **Contract Types Supported**

- **Securities Purchase Agreements** - Stock and warrant issuances
- **License Agreements** - IP licensing with royalty terms
- **Employment Agreements** - Executive compensation
- **Settlement Agreements** - Legal dispute resolutions
- **Rights Agreements** - Investor and registration rights

### **Graph Schema**

```
(Company:Party)-[:PARTY_TO]->(Contract:SecuritiesContract)
(Investor:Party)-[:PARTY_TO]->(Contract:SecuritiesContract)
(Contract)-[:ISSUES_SECURITY]->(Security:Security)
(Contract)-[:HAS_CONDITIONS]->(Condition:ClosingConditions)
(Contract)-[:HAS_REGISTRATION_RIGHTS]->(Rights:RegistrationRights)
```

## 🎯 **Example Queries**

The system can answer complex questions like:

- *"What securities purchase agreements were executed in 2022?"*
- *"Show me all license agreements with REGENXBIO"*
- *"Find contracts with total offerings over $1 million"*
- *"What types of securities has Abeona issued over time?"*
- *"Which contracts include warrant issuances?"*
- *"Show closing conditions across all agreements"*

## 💾 **Smart Caching System**

### **Automatic LLM Cost Optimization**

```bash
# First run: Processes all contracts with LLM
python pipeline.py

# Second run: Uses cached data, no LLM calls!
python pipeline.py
🏃‍♂️ 61 already processed (will use cache)
🤖 0 new files (will use LLM processing)
```

### **Cache Management**

- **Main Cache**: `processed_contracts_cache.json`
- **Backups**: `processed_contracts_cache_backup_YYYYMMDD_HHMMSS.json`
- **Smart Updates**: Only reprocesses if files were modified
- **Continuous Saves**: Auto-saves every 5 contracts

### **Force Reprocessing**

```python
from src.batch_ingest_contracts import EnhancedBatchProcessor
processor = EnhancedBatchProcessor()

# Reprocess everything with enhanced extraction
processor.run_batch_processing(force_reprocess=True)
```

## 🔌 **Integration Options**

### **Custom Contract Processing**

```python
from src.securities_pipeline_runner import SecuritiesGraphRAGPipeline

pipeline = SecuritiesGraphRAGPipeline()

# Process your contract
contract_text = open("your_contract.html").read()
contract_data = pipeline.ingest_contract(contract_text, "custom_id")
```

### **Direct Querying**

```python
# Natural language queries
result = pipeline.query_contracts("Find all warrant agreements")
print(result)
```

### **Advanced Analytics**

```python
# Database statistics
stats = pipeline.get_database_stats()
print(f"Total contracts: {stats['total_contracts']}")
print(f"Securities issued: {stats['total_securities']}")
```

## 📈 **Database Management**

### **Neo4j Browser Access**

Visit: `http://localhost:7474`

- Username: `neo4j`
- Password: `graphrag_password`

### **Sample Cypher Queries**

```cypher
// All securities contracts
MATCH (c:SecuritiesContract) 
RETURN c.title, c.contract_type, c.execution_date 
ORDER BY c.execution_date DESC

// Securities by type
MATCH (c:SecuritiesContract)-[:ISSUES_SECURITY]->(s:Security)
RETURN s.security_type, count(*) as count
ORDER BY count DESC

// Parties and their roles
MATCH (p:Party)-[:PARTY_TO]->(c:SecuritiesContract)
RETURN p.name, p.role, count(c) as contract_count
ORDER BY contract_count DESC

// Financial analysis
MATCH (c:SecuritiesContract)
WHERE c.total_offering_amount IS NOT NULL
RETURN c.execution_date, c.total_offering_amount, c.title
ORDER BY c.total_offering_amount DESC

// License agreements with royalty info
MATCH (c:SecuritiesContract)
WHERE c.contract_type = "License Agreement"
RETURN c.title, c.execution_date, c.summary
```

## 🔧 **Troubleshooting**

### **Common Issues**

1. **Rate Limit Errors**
   ```bash
   # The system now uses gemini-1.5-flash with higher limits
   # Cache prevents redundant API calls
   ```

2. **Neo4j Connection Error**
   ```bash
   # Check if Neo4j is running
   docker ps | grep neo4j
   
   # Restart if needed
   cd config && docker-compose restart
   ```

3. **API Key Issues**
   ```bash
   # Verify environment variable
   echo $GOOGLE_API_KEY
   
   # Test API access
   python -c "from langchain_google_genai import ChatGoogleGenerativeAI; print('API OK')"
   ```

### **Development Mode**

```bash
# Test enhanced extraction on sample contracts
python -c "
from src.securities_extraction import SecuritiesContractExtractor
extractor = SecuritiesContractExtractor()
# Test your extraction logic
"

# Interactive mode with existing data
python -c "
from src.securities_pipeline_runner import SecuritiesGraphRAGPipeline
pipeline = SecuritiesGraphRAGPipeline()
result = pipeline.query_contracts('your query here')
print(result)
"
```

## 🚀 **Advanced Features**

### **Enhanced Extraction**

- **Hybrid AI + Rule-Based**: Combines LLM understanding with precise regex patterns
- **Smart Date Detection**: Multiple date format recognition
- **Financial Term Extraction**: Aggregate purchase prices, per-share amounts
- **Party Intelligence**: Entity types, jurisdictions, roles
- **Securities Details**: Stock types, quantities, exercise prices
- **Closing Conditions**: Automatic detection of common conditions

### **Automatic Backups**

```bash
# Neo4j database backups
ls neo4j_backups/
neo4j_backup_20241226_133704.zip
working_backup.zip

# Processed contracts cache backups  
ls processed_contracts_cache_backup_*.json
```

### **Batch Reports**

```bash
# Detailed processing reports
ls *_batch_report_*.json
abeona_batch_report_20241226_133709.json
```

## 📊 **Data Quality Improvements**

### **Before Enhancements:**
- ❌ Many "Basic extraction - full parsing failed" summaries
- ❌ Null execution dates and financial amounts
- ❌ Empty securities and conditions arrays

### **After Enhancements:**
- ✅ Meaningful contract summaries with transaction details
- ✅ Extracted execution dates from various formats  
- ✅ Financial amounts detected (purchase prices, offerings)
- ✅ Securities information (types, quantities, prices)
- ✅ Closing conditions automatically identified

## 📁 **Project Structure**

```
graphrag/
├── data/ABEONA-THERAPEUTICS-INC/     # 61 contract files (1996-2023)
├── src/                              # Core system modules
├── config/                           # Docker and Neo4j configuration
├── neo4j_backups/                    # Database backups
├── reports/                          # Processing reports
├── pipeline.py                       # Main execution script
├── processed_contracts_cache.json    # Smart caching system
└── IMPROVEMENTS_SUMMARY.md           # Detailed enhancement documentation
```

## 📝 **License**

MIT License - See LICENSE file for details.

## 🤝 **Contributing**

1. Fork the repository
2. Create a feature branch  
3. Add tests for new contract types
4. Submit a pull request

---

**Built with:** LangChain, LangGraph, Neo4j, Google Gemini AI, Pydantic, and intelligent caching for cost-effective securities contract analysis. 