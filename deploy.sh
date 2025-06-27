#!/bin/bash

# GraphRAG Deployment Script
set -e

echo "🚀 Starting GraphRAG Deployment..."

# Check if .env exists
if [ ! -f .env ]; then
    echo "⚠️  Creating .env file from template..."
    cp .env.example .env
    echo "📝 Please edit .env file with your configuration before continuing."
    exit 1
fi

# Load environment variables
source .env

# Build and start services
echo "🏗️  Building services..."
docker-compose -f docker-compose.prod.yml build

echo "🔧 Starting Neo4j database..."
docker-compose -f docker-compose.prod.yml up -d neo4j

# Wait for Neo4j to be ready
echo "⏳ Waiting for Neo4j to be ready..."
sleep 30

# Test Neo4j connection
echo "🔍 Testing Neo4j connection..."
until docker exec graphrag-neo4j-prod cypher-shell -u neo4j -p graphrag_secure_password_2024 "RETURN 1 as test;" > /dev/null 2>&1; do
    echo "Neo4j not ready yet... waiting 10 seconds"
    sleep 10
done

echo "✅ Neo4j is ready!"

# Start backend
echo "🖥️  Starting backend API..."
docker-compose -f docker-compose.prod.yml up -d backend

# Wait for backend to be ready
echo "⏳ Waiting for backend to be ready..."
sleep 20

# Test backend connection
echo "🔍 Testing backend connection..."
until curl -f http://localhost:8000/ > /dev/null 2>&1; do
    echo "Backend not ready yet... waiting 10 seconds"
    sleep 10
done

echo "✅ Backend is ready!"

# Show status
echo "📊 Service Status:"
docker-compose -f docker-compose.prod.yml ps

echo ""
echo "🎉 Deployment Complete!"
echo "📱 Frontend: Deploy to Vercel using the frontend/ directory"
echo "🖥️  Backend API: http://localhost:8000"
echo "🗃️  Neo4j Browser: http://localhost:7474"
echo "🔑 Neo4j Credentials: neo4j / graphrag_secure_password_2024"
echo ""
echo "📋 Next Steps:"
echo "1. Deploy frontend to Vercel"
echo "2. Update NEXT_PUBLIC_API_BASE_URL in Vercel environment"
echo "3. Configure your domain and SSL"
echo "4. Test the complete application"
echo ""
echo "🛠️  To stop services: docker-compose -f docker-compose.prod.yml down"
echo "🗑️  To remove volumes: docker-compose -f docker-compose.prod.yml down -v" 