# ABEONA THERAPEUTICS - ENHANCED GRAPHRAG SYSTEM

## 🎯 Overview

This system processes **all 61 securities contracts** from Abeona Therapeutics (1996-2023) into a comprehensive knowledge graph using GraphRAG technology. It handles multiple contract types including securities purchase agreements, license agreements, settlement agreements, employment letters, and lease agreements.

## 🏗️ System Architecture

### Core Components

1. **Enhanced Batch Processor** (`batch_ingest_contracts.py`)
   - Processes all 61 contract files (HTML and TXT formats)
   - Intelligent contract type detection
   - Progress tracking and error handling
   - Comprehensive reporting

2. **Securities Pipeline Runner** (`securities_pipeline_runner.py`)
   - Complete GraphRAG pipeline orchestration
   - Neo4j knowledge graph integration
   - Advanced text cleaning and preprocessing
   - Natural language querying interface

3. **Enhanced Contract Extractor** (`securities_extraction.py`)
   - AI-powered contract data extraction using Gemini
   - Specialized extraction for different contract types
   - Robust error handling and fallback mechanisms
   - Structured data output

4. **Securities Data Models** (`securities_data_models.py`)
   - Comprehensive Pydantic models for all contract types
   - Support for parties, securities, closing conditions
   - Registration rights and legal provisions

5. **Direct Query Agent** (`direct_securities_agent.py`)
   - Simple querying interface for the knowledge graph
   - Real-time contract analysis
   - Database statistics and reporting

## 📊 Contract Coverage

The system processes **61 contracts** spanning **27 years** (1996-2023):

- **HTML Files**: 13 contracts (recent years)
- **TXT Files**: 48 contracts (earlier years)
- **Contract Types**:
  - Securities Purchase Agreements
  - License Agreements  
  - Settlement Agreements
  - Employment Letters
  - Lease Agreements
  - Rights Agreements
  - Warrant Agreements

### Contract Distribution by Year
- 1996-2000: Early stage contracts (18 files)
- 2001-2010: Growth period contracts (15 files) 
- 2011-2015: Expansion contracts (8 files)
- 2019-2023: Recent contracts (20 files)

## 🚀 Getting Started

### Prerequisites

1. **Environment Setup**
```bash
# Create .env file with:
GOOGLE_API_KEY=your_gemini_api_key
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_neo4j_password
```

2. **Required Dependencies**
```bash
pip install langchain_google_genai neo4j pydantic beautifulsoup4 python-dotenv
```

3. **Neo4j Database**
   - Install and start Neo4j
   - Create database with authentication

### Running the System

#### Option 1: Complete Batch Processing (Recommended)
```bash
python run_batch_processing.py
```

**Features:**
- ✅ Environment validation
- ✅ Dependency checking  
- ✅ All 61 contracts processing
- ✅ Progress tracking
- ✅ Interactive query session
- ✅ Comprehensive reporting

#### Option 2: Direct Batch Processing
```bash
python batch_ingest_contracts.py
```

#### Option 3: Testing Individual Components
```bash
python test_system.py
```

## 🔍 System Features for Maximum Effectiveness

### 1. **Intelligent Contract Type Detection**
- Automatically identifies contract types from content
- Specialized extraction prompts for each type
- Handles diverse legal document formats

### 2. **Advanced Text Processing**
- HTML parsing with BeautifulSoup
- Document metadata extraction and cleaning
- Smart truncation preserving key sections
- Unicode and formatting normalization

### 3. **Comprehensive Knowledge Graph**
- **Nodes**: Contracts, Parties, Securities, Conditions, Representations
- **Relationships**: PARTY_TO, ISSUES_SECURITY, HAS_CLOSING_CONDITION
- **Properties**: Financial terms, dates, legal provisions
- **Indexes**: Optimized for fast querying

### 4. **Robust Error Handling**
- Graceful degradation for parsing failures
- Basic information extraction as fallback
- Detailed error reporting and logging
- Recovery mechanisms for partial failures

### 5. **Performance Optimization**
- Parallel processing capabilities
- Database connection pooling
- Efficient memory management
- Progress tracking and rate monitoring

### 6. **Advanced Querying**
- Natural language queries using Gemini
- Structured Cypher query generation
- Cross-contract analysis and comparison
- Financial term aggregation and analysis

## 🎯 Query Examples

### Financial Analysis
```
"What are the total offering amounts across all securities purchase agreements?"
"Compare purchase prices per share over different years"
"Show me all contracts with offering amounts over $1 million"
```

### Party Analysis
```
"Who are the key investors in Abeona Therapeutics?"
"What companies has Abeona licensed technology from?"
"Show me all settlement agreements and the parties involved"
```

### Contract Evolution
```
"How have Abeona's securities offerings changed over time?"
"What types of registration rights were granted in recent contracts?"
"Compare employment agreements from different periods"
```

### Legal Provisions
```
"What closing conditions are common across purchase agreements?"
"Show me all license agreements and their key terms"
"What SEC exemptions were used in different offerings?"
```

## 📈 Database Schema

### Node Types
- **SecuritiesContract**: Core contract information
- **Party**: Companies, individuals, entities involved
- **Security**: Stocks, warrants, options issued
- **ClosingCondition**: Requirements for deal completion
- **Representation**: Legal representations and warranties
- **RegistrationRights**: SEC registration provisions

### Key Properties
- **Financial**: Offering amounts, prices, exercise prices
- **Temporal**: Execution dates, closing dates, deadlines
- **Legal**: Governing law, SEC exemptions, registration status
- **Categorical**: Contract types, party roles, security types

## 🛡️ Error Recovery and Fallbacks

### Parsing Failures
- Extract basic information using regex patterns
- Identify parties from contract structure
- Determine contract type from keywords
- Create minimal but useful contract records

### Database Issues
- Connection retry mechanisms
- Transaction rollback on failures
- Graceful degradation to local processing
- Detailed error reporting

### API Limitations
- Rate limiting and backoff strategies
- Context window management for large documents
- Alternative extraction methods for edge cases

## 📊 Reporting and Analytics

### Batch Processing Report
- Success/failure rates
- Processing time and throughput
- Database growth statistics
- Error analysis and categorization

### Contract Analytics
- Financial term distributions
- Party relationship networks
- Temporal trend analysis
- Legal provision frequencies

## 🔧 Customization and Extension

### Adding New Contract Types
1. Update contract type detection in `_detect_contract_type()`
2. Add specialized extraction method
3. Update data models if needed
4. Test with sample contracts

### Enhancing Extraction
1. Modify prompts in extraction methods
2. Add new data fields to models
3. Update database schema and relationships
4. Implement new query patterns

### Scaling for Larger Datasets
1. Implement batch processing optimizations
2. Add database partitioning strategies
3. Use distributed processing frameworks
4. Implement caching mechanisms

## 🎯 System Effectiveness Features

### 1. **Multi-Format Support**
- Handles both HTML and TXT contract formats
- Robust parsing for different document structures
- Metadata extraction from file paths and naming

### 2. **Temporal Analysis**
- 27-year contract history processing
- Evolution tracking of contract terms
- Historical trend analysis capabilities

### 3. **Financial Intelligence**
- Automatic extraction of monetary terms
- Price and valuation trend analysis
- Investment round tracking

### 4. **Legal Compliance Tracking**
- SEC exemption analysis
- Registration rights monitoring
- Regulatory compliance patterns

### 5. **Relationship Mapping**
- Party interaction networks
- Corporate relationship evolution
- Investment ecosystem analysis

## 🚀 Next Steps for Maximum Effectiveness

1. **Run Complete Processing**: Process all 61 contracts
2. **Analyze Results**: Review success rates and data quality
3. **Refine Extraction**: Improve prompts based on results
4. **Enhanced Querying**: Develop specialized query templates
5. **Visualization**: Add graph visualization capabilities
6. **API Development**: Create REST API for external access

---

*This system represents a comprehensive GraphRAG implementation optimized for securities contract analysis, providing powerful insights into Abeona Therapeutics' corporate history and legal relationships.* 