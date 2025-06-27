#!/bin/bash

echo "🚀 Starting GraphRAG Full Stack Application"
echo "============================================"

# Function to handle cleanup
cleanup() {
    echo ""
    echo "🛑 Shutting down services..."
    kill $(jobs -p) 2>/dev/null
    exit 0
}

# Set trap to handle Ctrl+C
trap cleanup INT

# Check if tmux is available (for better terminal management)
if command -v tmux &> /dev/null; then
    echo "📱 Using tmux for session management..."
    
    # Create new tmux session
    tmux new-session -d -s graphrag-app
    
    # Split the window
    tmux split-window -h
    
    # Start backend in left pane
    tmux send-keys -t 0 './start_backend.sh' Enter
    
    # Start frontend in right pane
    tmux send-keys -t 1 './start_frontend.sh' Enter
    
    # Attach to the session
    echo "🎯 Attaching to tmux session..."
    echo "Use 'Ctrl+B' then 'D' to detach, 'tmux attach -t graphrag-app' to reattach"
    tmux attach-session -t graphrag-app
    
else
    echo "📱 Starting services in background..."
    
    # Start backend in background
    echo "🔧 Starting backend API server..."
    ./start_backend.sh &
    BACKEND_PID=$!
    
    # Wait a bit for backend to start
    sleep 5
    
    # Start frontend in background
    echo "🎨 Starting frontend development server..."
    ./start_frontend.sh &
    FRONTEND_PID=$!
    
    echo ""
    echo "✅ Services started!"
    echo "📊 Backend API: http://localhost:8000"
    echo "🌐 Frontend App: http://localhost:3000"
    echo "📚 API Docs: http://localhost:8000/docs"
    echo ""
    echo "Press Ctrl+C to stop all services"
    
    # Wait for user interrupt
    wait
fi 