#!/bin/bash

echo "🚀 Starting GraphRAG Frontend Development Server"
echo "================================================"

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed. Please install Node.js first."
    echo "Visit: https://nodejs.org/"
    exit 1
fi

# Navigate to frontend directory
cd frontend

# Check if package.json exists
if [ ! -f "package.json" ]; then
    echo "❌ package.json not found. Make sure you're in the correct directory."
    exit 1
fi

# Install dependencies if node_modules doesn't exist
if [ ! -d "node_modules" ]; then
    echo "📦 Installing dependencies..."
    npm install
fi

# Set environment variables
export NEXT_PUBLIC_API_BASE_URL=http://localhost:8000

echo "🌐 Starting Next.js development server..."
echo "Frontend will be available at: http://localhost:3000"
echo "API Backend should be running at: http://localhost:8000"
echo ""
echo "Press Ctrl+C to stop the server"

# Start the development server
npm run dev 