# 🚀 GraphRAG Deployment Guide

Complete guide for deploying your GraphRAG Contract Analysis application to production.

## 🏗️ **Architecture Options**

### **Option 1: Simple & Cost-Effective (Recommended)**
- **Frontend**: Vercel (Free)
- **Backend**: Railway/Render (Free tier)
- **Database**: Neo4j AuraDB Free
- **Cost**: $0-20/month

### **Option 2: Professional Setup**
- **Frontend**: Vercel Pro
- **Backend**: DigitalOcean App Platform
- **Database**: Neo4j AuraDB Professional
- **Cost**: $50-150/month

### **Option 3: Enterprise/Self-Hosted**
- **Frontend**: Vercel/CloudFlare Pages
- **Backend**: AWS ECS/Google Cloud Run
- **Database**: Self-hosted Neo4j cluster
- **Cost**: $200+/month

---

## 🌐 **Option 1: Simple Deployment (Recommended)**

### **Step 1: Deploy Database (Neo4j AuraDB)**

1. **Create Account**: Go to [Neo4j AuraDB](https://neo4j.com/cloud/aura/)
2. **Create Instance**: 
   - Choose "AuraDB Free"
   - Region: Choose closest to your users
   - Database name: `graphrag-contracts`
3. **Save Credentials**: Download connection details
4. **Note Connection String**: `neo4j+s://xxxxxxx.databases.neo4j.io`

### **Step 2: Deploy Backend (Railway)**

1. **Create Account**: Go to [Railway](https://railway.app)
2. **New Project**: 
   - Connect your GitHub repository
   - Select the backend folder
3. **Environment Variables**:
   ```bash
   NEO4J_URI=neo4j+s://your-aura-url.databases.neo4j.io
   NEO4J_USER=neo4j
   NEO4J_PASSWORD=your-aura-password
   PORT=8000
   ```
4. **Deploy**: Railway auto-deploys from your repository
5. **Get URL**: Note your Railway app URL (e.g., `https://your-app.railway.app`)

### **Step 3: Deploy Frontend (Vercel)**

1. **Create Account**: Go to [Vercel](https://vercel.com)
2. **Import Project**: 
   - Connect GitHub repository
   - Select the `frontend` folder as root
3. **Environment Variables**:
   ```bash
   NEXT_PUBLIC_API_BASE_URL=https://your-railway-app.railway.app
   ```
4. **Deploy**: Vercel automatically builds and deploys
5. **Custom Domain**: Add your domain in Vercel settings

### **Total Time**: ~30 minutes
### **Total Cost**: $0 (Free tiers)

---

## 🏢 **Option 2: Professional Deployment**

### **Step 1: Deploy Database (Neo4j AuraDB Professional)**

1. **Upgrade to AuraDB Professional**: Better performance and support
2. **Configure**:
   - Memory: 8GB
   - Storage: 50GB
   - Backup: Daily
3. **Security**: Enable IP whitelist, VPC if needed

### **Step 2: Deploy Backend (DigitalOcean)**

1. **Create Droplet**: 
   - 2 vCPUs, 4GB RAM
   - Ubuntu 22.04
   - $24/month
2. **Setup Docker**:
   ```bash
   # Install Docker
   curl -fsSL https://get.docker.com -o get-docker.sh
   sh get-docker.sh
   
   # Install Docker Compose
   sudo apt update
   sudo apt install docker-compose-plugin
   ```
3. **Clone and Deploy**:
   ```bash
   git clone your-repository
   cd graphrag
   cp .env.example .env
   # Edit .env with your Neo4j credentials
   ./deploy.sh
   ```
4. **Configure Nginx** (reverse proxy):
   ```nginx
   server {
       listen 80;
       server_name your-api-domain.com;
       
       location / {
           proxy_pass http://localhost:8000;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
       }
   }
   ```
5. **SSL Certificate**:
   ```bash
   sudo apt install certbot python3-certbot-nginx
   sudo certbot --nginx -d your-api-domain.com
   ```

### **Step 3: Deploy Frontend (Vercel Pro)**

1. **Upgrade to Vercel Pro**: Better performance, analytics
2. **Configure**:
   ```bash
   NEXT_PUBLIC_API_BASE_URL=https://your-api-domain.com
   ```
3. **Custom Domain**: Configure with SSL

### **Total Time**: ~2 hours
### **Total Cost**: ~$100/month

---

## 🏭 **Option 3: Enterprise Self-Hosted**

### **Step 1: Infrastructure Setup**

#### **AWS ECS Deployment**
```yaml
# docker-compose.aws.yml
version: '3.8'
services:
  backend:
    image: your-ecr-repo/graphrag-backend:latest
    ports:
      - "8000:8000"
    environment:
      - NEO4J_URI=${NEO4J_URI}
      - NEO4J_USER=${NEO4J_USER}
      - NEO4J_PASSWORD=${NEO4J_PASSWORD}
    deploy:
      replicas: 3
      resources:
        reservations:
          cpus: '1'
          memory: 2G
```

#### **Kubernetes Deployment**
```yaml
# k8s-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: graphrag-backend
spec:
  replicas: 3
  selector:
    matchLabels:
      app: graphrag-backend
  template:
    spec:
      containers:
      - name: backend
        image: your-registry/graphrag-backend:latest
        ports:
        - containerPort: 8000
        env:
        - name: NEO4J_URI
          valueFrom:
            secretKeyRef:
              name: neo4j-secret
              key: uri
```

### **Step 2: Database Cluster**

#### **Neo4j Cluster Setup**
```bash
# Core servers (3 minimum)
docker run -d --name neo4j-core-1 \
  -e NEO4J_AUTH=neo4j/password \
  -e NEO4J_dbms_mode=CORE \
  -e NEO4J_causal__clustering_initial__discovery__members=neo4j-core-1:5000,neo4j-core-2:5000,neo4j-core-3:5000 \
  neo4j:5.20-enterprise

# Read replicas (optional)
docker run -d --name neo4j-replica-1 \
  -e NEO4J_AUTH=neo4j/password \
  -e NEO4J_dbms_mode=READ_REPLICA \
  -e NEO4J_causal__clustering_initial__discovery__members=neo4j-core-1:5000,neo4j-core-2:5000,neo4j-core-3:5000 \
  neo4j:5.20-enterprise
```

### **Step 3: CI/CD Pipeline**

```yaml
# .github/workflows/deploy.yml
name: Deploy to Production

on:
  push:
    branches: [main]

jobs:
  deploy-backend:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    
    - name: Build and push Docker image
      run: |
        docker build -t ${{ secrets.ECR_REGISTRY }}/graphrag-backend:${{ github.sha }} ./backend
        docker push ${{ secrets.ECR_REGISTRY }}/graphrag-backend:${{ github.sha }}
    
    - name: Deploy to ECS
      run: |
        aws ecs update-service --cluster graphrag --service graphrag-backend --force-new-deployment

  deploy-frontend:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    
    - name: Deploy to Vercel
      uses: amondnet/vercel-action@v25
      with:
        vercel-token: ${{ secrets.VERCEL_TOKEN }}
        vercel-org-id: ${{ secrets.ORG_ID }}
        vercel-project-id: ${{ secrets.PROJECT_ID }}
        working-directory: ./frontend
```

---

## 🔧 **Environment Configuration**

### **Production Environment Variables**

#### **Backend (.env)**
```bash
# Database
NEO4J_URI=neo4j+s://your-instance.databases.neo4j.io
NEO4J_USER=neo4j
NEO4J_PASSWORD=your-secure-password

# Security
ENVIRONMENT=production
ALLOWED_ORIGINS=https://your-frontend-domain.com

# Performance
WORKERS=4
MAX_UPLOAD_SIZE=50MB
CACHE_TTL=3600

# Monitoring (optional)
SENTRY_DSN=your-sentry-dsn
LOG_LEVEL=INFO
```

#### **Frontend (.env.local)**
```bash
# API Configuration
NEXT_PUBLIC_API_BASE_URL=https://your-api-domain.com

# Analytics (optional)
NEXT_PUBLIC_GOOGLE_ANALYTICS=GA-XXXXXXXXX
NEXT_PUBLIC_SENTRY_DSN=your-frontend-sentry-dsn

# Features
NEXT_PUBLIC_MAX_FILE_SIZE=50
NEXT_PUBLIC_SUPPORTED_FORMATS=html,txt
```

---

## 🛡️ **Security Best Practices**

### **1. API Security**
```python
# backend/api.py - Add security headers
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware

app.add_middleware(HTTPSRedirectMiddleware)
app.add_middleware(TrustedHostMiddleware, allowed_hosts=["your-domain.com"])
```

### **2. Rate Limiting**
```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

@app.post("/upload")
@limiter.limit("5/minute")
async def upload_contracts(request: Request, ...):
    # Implementation
```

### **3. Input Validation**
```python
from pydantic import BaseModel, validator, Field

class ContractUpload(BaseModel):
    filename: str = Field(..., max_length=255)
    
    @validator('filename')
    def validate_filename(cls, v):
        if not v.endswith(('.html', '.txt')):
            raise ValueError('Invalid file type')
        return v
```

### **4. Database Security**
- Use SSL connections (`neo4j+s://`)
- Strong passwords (min 16 characters)
- IP whitelist for database access
- Regular security updates

---

## 📊 **Monitoring & Observability**

### **1. Application Monitoring**
```python
# Add to requirements.txt
sentry-sdk[fastapi]==1.32.0

# backend/api.py
import sentry_sdk
sentry_sdk.init(
    dsn="your-sentry-dsn",
    traces_sample_rate=1.0,
)
```

### **2. Health Checks**
```python
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    }
```

### **3. Logging**
```python
import logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
```

---

## 💰 **Cost Optimization**

### **Free Tier Limits**
- **Vercel**: 100GB bandwidth, unlimited requests
- **Railway**: 500 hours/month, 1GB RAM
- **Neo4j AuraDB Free**: 50k nodes, 175k relationships

### **Scaling Strategies**
1. **Start Small**: Use free tiers for MVP
2. **Monitor Usage**: Track bandwidth, storage, compute
3. **Optimize Caching**: Reduce API calls and database queries
4. **CDN**: Use Vercel's global CDN for static assets

### **Monthly Cost Estimates**
| Tier | Frontend | Backend | Database | Total |
|------|----------|---------|----------|-------|
| Free | $0 | $0 | $0 | $0 |
| Starter | $20 | $25 | $50 | $95 |
| Professional | $20 | $100 | $200 | $320 |
| Enterprise | $400+ | $500+ | $1000+ | $1900+ |

---

## 🚨 **Troubleshooting**

### **Common Issues**

1. **CORS Errors**
   ```python
   # backend/api.py
   app.add_middleware(
       CORSMiddleware,
       allow_origins=["https://your-frontend-domain.com"],
       allow_credentials=True,
       allow_methods=["*"],
       allow_headers=["*"],
   )
   ```

2. **Database Connection**
   ```python
   # Test connection
   from neo4j import GraphDatabase
   driver = GraphDatabase.driver(uri, auth=(user, password))
   driver.verify_connectivity()
   ```

3. **File Upload Issues**
   - Check file size limits
   - Verify MIME types
   - Ensure proper error handling

4. **Performance Issues**
   - Enable caching
   - Optimize database queries
   - Use connection pooling

### **Debug Commands**
```bash
# Check service status
docker-compose ps

# View logs
docker-compose logs backend
docker-compose logs neo4j

# Test API endpoints
curl -f https://your-api-domain.com/health

# Monitor resources
docker stats
```

---

## ✅ **Deployment Checklist**

### **Pre-Deployment**
- [ ] Environment variables configured
- [ ] SSL certificates ready
- [ ] Database backups tested
- [ ] Security headers implemented
- [ ] Rate limiting configured

### **Deployment**
- [ ] Frontend deployed to Vercel
- [ ] Backend deployed and healthy
- [ ] Database accessible and secure
- [ ] Domain/DNS configured
- [ ] SSL certificates active

### **Post-Deployment**
- [ ] Health checks passing
- [ ] Monitoring configured
- [ ] Error tracking active
- [ ] Performance metrics baseline
- [ ] User acceptance testing

### **Ongoing Maintenance**
- [ ] Regular security updates
- [ ] Database backups verified
- [ ] Performance monitoring
- [ ] Cost optimization reviews
- [ ] User feedback incorporation

---

## 🎯 **Quick Start Command**

For the simplest deployment:

```bash
# 1. Clone repository
git clone your-repo
cd graphrag

# 2. Setup environment
cp .env.example .env
# Edit .env with your settings

# 3. Deploy locally first
./deploy.sh

# 4. Deploy to cloud
# - Push to GitHub
# - Connect Vercel to frontend/
# - Connect Railway to backend/
# - Configure Neo4j AuraDB

# 5. Update environment variables in cloud platforms
```

**Total deployment time: 30-60 minutes** 🚀

Need help? Check the troubleshooting section or open an issue! 