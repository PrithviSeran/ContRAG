#!/bin/bash

echo "🚀 Starting GraphRAG Backend API Server"
echo "========================================"

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3 first."
    exit 1
fi

# Navigate to backend directory
cd backend

# Check if virtual environment exists, create if not
if [ ! -d "venv" ]; then
    echo "📦 Creating Python virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🐍 Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "📦 Installing Python dependencies..."
pip install -r requirements.txt

# Check if .env file exists
if [ ! -f "../.env" ]; then
    echo "⚠️  Warning: .env file not found in root directory."
    echo "Please make sure you have configured your environment variables."
    echo "Required variables:"
    echo "- GOOGLE_API_KEY"
    echo "- NEO4J_URI"
    echo "- NEO4J_USER"
    echo "- NEO4J_PASSWORD"
    echo ""
fi

echo "🌐 Starting FastAPI server..."
echo "API will be available at: http://localhost:8000"
echo "API documentation: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop the server"

# Start the API server using uvicorn directly for better WebSocket support
uvicorn api:app --host 0.0.0.0 --port 8000 --reload 