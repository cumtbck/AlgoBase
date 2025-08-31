#!/bin/bash

# CLAUDE Quick Start Script

echo "🚀 Starting CLAUDE Application..."

# Check if we're in the right directory
if [ ! -f "CLAUDE/README.md" ]; then
    echo "❌ Error: Please run this script from the AlgoBase directory"
    exit 1
fi

cd CLAUDE

echo "📁 Working directory: $(pwd)"

# Function to cleanup background processes
cleanup() {
    echo "🛑 Shutting down CLAUDE..."
    if [ ! -z "$BACKEND_PID" ]; then
        kill $BACKEND_PID 2>/dev/null
    fi
    exit 0
}

trap cleanup SIGINT SIGTERM

# Setup backend
echo "⚙️  Setting up backend..."
cd backend

# Check for conda
if command -v conda &> /dev/null; then
    echo "📦 Using conda environment..."
    CONDA_ENV_NAME="claude_env"
    
    # Create environment if it doesn't exist
    if ! conda env list | grep -q "^$CONDA_ENV_NAME\s"; then
        echo "Creating conda environment: $CONDA_ENV_NAME"
        conda create -n $CONDA_ENV_NAME python=3.10 -y
    fi
    
    # Activate environment
    source "$(conda info --base)/etc/profile.d/conda.sh"
    conda activate $CONDA_ENV_NAME
else
    echo "📦 Using virtual environment..."
    if [ ! -d "venv" ]; then
        echo "Creating virtual environment..."
        python3 -m venv venv
    fi
    source venv/bin/activate
fi

# Install dependencies
echo "📚 Installing dependencies..."
pip install --upgrade pip
pip install fastapi uvicorn pydantic python-multipart
pip install langchain langchain-community ollama chromadb
pip install sentence-transformers transformers torch accelerate
pip install python-dotenv pydantic-settings aiofiles httpx websockets
pip install watchdog

# Copy environment file
if [ ! -f ".env" ]; then
    cp .env.example .env
    echo "📝 Environment file created"
fi

# Start backend
echo "🔧 Starting backend server..."
python main.py &
BACKEND_PID=$!

# Wait for backend
echo "⏳ Waiting for backend to start..."
sleep 5

# Check backend
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ Backend server started successfully"
else
    echo "⚠️  Backend server may have issues. Check console for errors."
fi

echo ""
echo "🖥️  Starting frontend application..."
cd ../frontend

# Open Xcode
if [ -f "CLAUDE.xcodeproj/project.pbxproj" ]; then
    open CLAUDE.xcodeproj
    echo "✅ Xcode project opened"
else
    echo "❌ Xcode project not found"
    cleanup
    exit 1
fi

echo ""
echo "🎉 CLAUDE Application started!"
echo ""
echo "📋 Instructions:"
echo "1. Build and run the app in Xcode"
echo "2. Backend API: http://localhost:8000"
echo "3. API Docs: http://localhost:8000/docs"
echo "4. Press Ctrl+C to stop backend"
echo ""
echo "🔧 If you have issues:"
echo "- Make sure Ollama is installed and running"
echo "- Download CodeLlama: ollama pull codellama:7b"
echo ""

# Keep script running
echo "Press Ctrl+C to exit..."
while true; do
    sleep 1
done