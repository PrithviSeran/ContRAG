# 📜 GraphRAG for Securities Contracts

A sophisticated **Graph Retrieval-Augmented Generation (GraphRAG)** system for analyzing securities purchase agreements, license agreements, and other financial contracts. Features a modern web interface with real-time processing updates and conversational AI for intelligent contract analysis.

## 🌐 **Live Demo**

**Try it now:** [https://cont-rag.vercel.app](https://cont-rag.vercel.app)

*No setup required! Just get a free [Google Gemini API key](https://makersuite.google.com/app/apikey) and start analyzing contracts.*

**✨ NEW: Web Interface with API Key Support for Easy Hosting**

## 🌐 **Web Interface Features**

- **🔑 Dynamic API Key Input** - Users provide their own Gemini API keys
- **📁 Drag & Drop Upload** - Easy contract file upload with progress tracking
- **⚡ Real-time Processing** - Live updates via WebSocket connections
- **💬 AI Chat Interface** - Natural language querying of processed contracts
- **📊 Contract Summaries** - Visual overview of processed documents
- **🔄 Session Management** - Clear distinction between current and historical data
- **🛡️ Secure & Private** - API keys stored locally in browser only

## 🚀 **Quick Start (Web Interface)**

### **For Hosted Deployment**

1. **Clone and Setup**
   ```bash
   git clone <repository>
   cd graphrag
   ```

2. **Backend Setup**
   ```bash
   # Install Python dependencies
   pip install -r requirements.txt
   
   # Start Neo4j database
   cd config && docker-compose up -d
   
   # Start backend API
   cd backend && python api.py
   ```

3. **Frontend Setup**
   ```bash
   # Install Node.js dependencies
   cd frontend
   npm install
   
   # Start development server
   npm run dev
   ```

4. **Access the Interface**
   - Open `http://localhost:3000`
   - Enter your Gemini API key (get free key from [Google AI Studio](https://makersuite.google.com/app/apikey))
   - Upload contracts and start processing!

### **For Local Development**

If you prefer command-line processing with environment variables:

```bash
# Create .env file
cp .env.example .env

# Add your API key
echo "GOOGLE_API_KEY=your_key_here" >> .env

# Run pipeline directly
python pipeline.py
```

## 🔧 **Architecture Overview**

```
Web Interface (Next.js) → FastAPI Backend → [Enhanced AI + Rule-Based Extraction] → Neo4j Graph Database
                               ↓
User Upload → Processing Pipeline → Structured Data → Knowledge Graph → AI Chat Interface
```

### **System Components**

| Component | Technology | Purpose |
|-----------|------------|---------|
| **Frontend** | Next.js + TypeScript | Modern web interface with real-time updates |
| **Backend** | FastAPI + Python | API server with WebSocket support |
| **Database** | Neo4j | Graph database for contract relationships |
| **AI Engine** | Google Gemini | Contract extraction and chat functionality |
| **Processing** | Custom Pipeline | Enhanced AI + rule-based extraction |

## 🔑 **API Key Management**

### **For Users (Hosted Sites)**

1. **Get Free API Key**: Visit [Google AI Studio](https://makersuite.google.com/app/apikey)
2. **Enter in Interface**: Paste key in the settings panel
3. **Validation**: System tests key before processing
4. **Security**: Keys stored locally in browser only

### **For Developers**

```bash
# Option 1: Environment variable (local development)
export GOOGLE_API_KEY="your_key_here"

# Option 2: .env file
echo "GOOGLE_API_KEY=your_key_here" > .env

# Option 3: Header in API requests (web interface)
curl -H "X-API-Key: your_key_here" http://localhost:8000/process
```

## 📱 **Web Interface Guide**

### **1. API Key Setup**
- First-time users see API key input screen
- Validate key before proceeding
- Keys saved in browser for future visits

### **2. Contract Upload**
- Drag & drop HTML/TXT contract files
- Duplicate detection and prevention
- Real-time upload progress

### **3. Processing Pipeline**
- Live status updates with WebSocket
- Progress tracking per file
- Detailed logging in sidebar

### **4. AI Chat Interface**
- Natural language queries
- Context-aware responses
- Chat history maintained
- Smart auto-scrolling

### **5. Contract Summary**
- Toggle between current session and all contracts
- Visual overview of processed documents
- Export capabilities

## 🎯 **API Endpoints**

### **Core Endpoints**

| Method | Endpoint | Purpose |
|--------|----------|---------|
| `POST` | `/validate-api-key` | Test API key validity |
| `POST` | `/upload` | Upload contract files |
| `POST` | `/process` | Start contract processing |
| `POST` | `/chat` | Chat with processed contracts |
| `GET` | `/contracts/summary` | Get contract summaries |
| `DELETE` | `/reset` | Clear system state |
| `WebSocket` | `/ws` | Real-time updates |

### **Authentication**

All endpoints accept API keys via:
```bash
# Header (recommended for web interface)
curl -H "X-API-Key: your_key_here" http://localhost:8000/process

# Environment variable (fallback for local development)
export GOOGLE_API_KEY="your_key_here"
```

## 🔍 **Contract Types Supported**

- **Securities Purchase Agreements** - Stock and warrant issuances
- **License Agreements** - IP licensing with royalty terms
- **Employment Agreements** - Executive compensation
- **Settlement Agreements** - Legal dispute resolutions
- **Rights Agreements** - Investor and registration rights

## 🤖 **Enhanced AI Extraction**

### **Hybrid Processing**
- **AI Understanding**: Gemini 1.5 Flash for context comprehension
- **Rule-Based Precision**: Regex patterns for financial data
- **Smart Caching**: Avoid reprocessing with intelligent cache system

### **Extracted Data Points**
- Contract titles and types
- Execution dates (multiple format support)
- Party information and roles
- Financial amounts and offerings
- Securities details (types, quantities, prices)
- Closing conditions and terms

### **Example Extraction**
```json
{
  "title": "Securities Purchase Agreement",
  "contract_type": "Securities Purchase Agreement",
  "execution_date": "2023-05-15",
  "parties": [
    {"name": "Abeona Therapeutics Inc.", "role": "Company"},
    {"name": "Institutional Investor", "role": "Purchaser"}
  ],
  "total_offering_amount": 5000000.0,
  "securities": [
    {
      "security_type": "Common Stock",
      "quantity": 1000000,
      "price_per_share": 5.0
    }
  ]
}
```

## 📊 **Graph Database Schema**

```cypher
// Core relationship patterns
(Company:Party)-[:PARTY_TO]->(Contract:SecuritiesContract)
(Investor:Party)-[:PARTY_TO]->(Contract:SecuritiesContract)
(Contract)-[:ISSUES_SECURITY]->(Security:Security)
(Contract)-[:HAS_CONDITIONS]->(Condition:ClosingConditions)
(Contract)-[:HAS_REGISTRATION_RIGHTS]->(Rights:RegistrationRights)
```

### **Sample Queries**

```cypher
// All securities contracts from 2023
MATCH (c:SecuritiesContract) 
WHERE c.execution_date CONTAINS "2023"
RETURN c.title, c.total_offering_amount 
ORDER BY c.execution_date DESC

// Top investors by contract count
MATCH (p:Party)-[:PARTY_TO]->(c:SecuritiesContract)
WHERE p.role = "Purchaser"
RETURN p.name, count(c) as contracts
ORDER BY contracts DESC LIMIT 10
```

## 🚀 **Deployment Options**

### **Local Development**
```bash
# Backend
cd backend && python api.py

# Frontend  
cd frontend && npm run dev

# Database
cd config && docker-compose up -d
```

### **Production Hosting**
```bash
# Backend (with gunicorn)
pip install gunicorn
gunicorn -w 4 -k uvicorn.workers.UvicornWorker backend.api:app

# Frontend (build and serve)
cd frontend
npm run build
npm start

# Database (persistent volumes)
docker-compose -f docker-compose.prod.yml up -d
```

### **Environment Variables**

#### **Backend (.env)**
```bash
# Optional: Default API key for local development
GOOGLE_API_KEY=your_default_key_here

# Neo4j Configuration
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=graphrag_password
```

#### **Frontend (.env.local)**
```bash
# API Base URL
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000

# For production
NEXT_PUBLIC_API_BASE_URL=https://your-api-domain.com
```

## 🛡️ **Security & Privacy**

### **API Key Handling**
- ✅ **Client-side storage**: Keys stored in browser localStorage only
- ✅ **No server persistence**: Never stored on backend servers
- ✅ **Secure transmission**: HTTPS recommended for production
- ✅ **Validation**: Real-time key testing before use
- ✅ **Transparency**: Clear privacy messaging for users

### **Data Protection**
- Contract files processed in memory
- Optional caching with user consent
- Neo4j database isolated and configurable
- WebSocket connections authenticated

## 📈 **Performance Features**

### **Smart Caching**
- Avoid redundant LLM processing
- Automatic backup creation
- Incremental updates only
- Cost optimization for hosted deployments

### **Real-time Updates**
- WebSocket connections for live progress
- Non-blocking processing pipeline
- Responsive UI during long operations
- Auto-scroll chat interface

### **Scalability**
- Stateless API design
- Containerized components
- Horizontal scaling support
- Database connection pooling

## 🔧 **Development Guide**

### **Adding New Contract Types**
```python
# 1. Update data models
class NewContractType(BaseModel):
    field1: str
    field2: Optional[float]

# 2. Add extraction logic
def extract_new_contract_type(text: str) -> NewContractType:
    # Implementation here
    pass

# 3. Update pipeline
# Add to securities_extraction.py
```

### **Custom Frontend Components**
```tsx
// Create new component in frontend/app/components/
import React from 'react'

interface CustomComponentProps {
  apiKey: string
  onUpdate: (data: any) => void
}

export default function CustomComponent({ apiKey, onUpdate }: CustomComponentProps) {
  // Implementation here
}
```

## 📁 **Project Structure**

```
graphrag/
├── frontend/                         # Next.js web interface
│   ├── app/                         
│   │   ├── components/              # React components
│   │   │   ├── ApiKeySettings.tsx   # API key management
│   │   │   ├── ChatInterface.tsx    # AI chat functionality
│   │   │   ├── ContractUploader.tsx # File upload interface
│   │   │   └── ...
│   │   ├── page.tsx                 # Main application page
│   │   └── layout.tsx               # App layout
│   ├── package.json                 # Node.js dependencies
│   └── ...
├── backend/                         # FastAPI backend
│   ├── api.py                       # Main API server
│   ├── uploads/                     # Temporary file storage
│   └── ...
├── src/                             # Core processing pipeline
│   ├── securities_extraction.py     # AI + rule-based extraction
│   ├── neo4j_persistence.py        # Database operations
│   ├── batch_ingest_contracts.py   # Batch processing
│   └── ...
├── config/                          # Docker configuration
│   ├── docker-compose.yml          # Local development
│   └── neo4j.conf                  # Database settings
├── pipeline.py                      # CLI processing script
└── README.md                        # This file
```

## 🤝 **Contributing**

1. **Fork** the repository
2. **Create** feature branch (`git checkout -b feature/amazing-feature`)
3. **Add** tests for new functionality
4. **Update** documentation
5. **Submit** pull request

### **Development Setup**
```bash
# Backend
cd backend
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows
pip install -r requirements.txt

# Frontend
cd frontend
npm install

# Database
cd config
docker-compose up -d
```

## 📄 **License**

MIT License - See LICENSE file for details.

---

**🚀 Ready to analyze contracts?** Get your free [Gemini API key](https://makersuite.google.com/app/apikey) and start processing!

**Built with:** Next.js, FastAPI, Neo4j, Google Gemini AI, TypeScript, Python, and modern web technologies for scalable contract analysis. 