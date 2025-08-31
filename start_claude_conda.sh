#!/bin/bash

# CLAUDE Application Launcher - Conda Version

echo "Starting CLAUDE Application..."

# Find the CLAUDE directory
if [ -f "CLAUDE/README.md" ]; then
    CLAUDE_DIR="CLAUDE"
elif [ -f "README.md" ] && [ -f "start.sh" ]; then
    CLAUDE_DIR="."
else
    echo "Error: Cannot find CLAUDE directory. Please run this script from a directory containing CLAUDE/ or from inside CLAUDE/"
    exit 1
fi

echo "Using CLAUDE directory: $CLAUDE_DIR"

# Function to cleanup background processes
cleanup() {
    echo "Shutting down CLAUDE..."
    if [ ! -z "$BACKEND_PID" ]; then
        kill $BACKEND_PID 2>/dev/null
    fi
    if [ ! -z "$CONDA_ENV_PID" ]; then
        kill $CONDA_ENV_PID 2>/dev/null
    fi
    exit 0
}

# Set up signal handlers
trap cleanup SIGINT SIGTERM

# Check if conda is installed
if ! command -v conda &> /dev/null; then
    echo "Error: conda is not installed. Please install Anaconda or Miniconda first."
    echo "Download from: https://docs.conda.io/en/latest/miniconda.html"
    exit 1
fi

# Start backend server
echo "Starting backend server..."
cd "$CLAUDE_DIR/backend"

# Conda environment name
CONDA_ENV_NAME="claude_env"

# Check if conda environment exists
if ! conda env list | grep -q "^$CONDA_ENV_NAME\s"; then
    echo "Creating conda environment: $CONDA_ENV_NAME"
    conda create -n $CONDA_ENV_NAME python=3.10 -y
    echo "Conda environment created successfully"
fi

# Activate conda environment
echo "Activating conda environment: $CONDA_ENV_NAME"
source "$(conda info --base)/etc/profile.d/conda.sh"
conda activate $CONDA_ENV_NAME

# Install dependencies
echo "Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Copy environment file if it doesn't exist
if [ ! -f ".env" ]; then
    cp .env.example .env
    echo "Environment file created. Please edit .env if needed."
fi

# Check if Ollama is installed
if ! command -v ollama &> /dev/null; then
    echo "Warning: Ollama is not installed. Please install Ollama to use LLM functionality:"
    echo "  brew install ollama"
    echo "  ollama serve"
    echo "  ollama pull codellama:7b"
    echo ""
fi

# Check if Ollama is running
if ! curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo "Warning: Ollama is not running. Please start it with: ollama serve"
    echo ""
fi

# Start backend in background
echo "Starting backend server..."
python main.py &
BACKEND_PID=$!

# Wait for backend to start
echo "Waiting for backend to start..."
sleep 5

# Check if backend is running
if ! curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "Warning: Backend server may not be running properly. Check the console for errors."
    echo "You can still try to start the frontend."
else
    echo "Backend server started successfully (PID: $BACKEND_PID)"
    echo "API available at: http://localhost:8000"
fi

# Start frontend application
echo ""
echo "Starting frontend application..."
cd ../frontend

# Check if Xcode project exists
if [ ! -f "CLAUDE.xcodeproj/project.pbxproj" ]; then
    echo "Error: Xcode project not found"
    cleanup
    exit 1
fi

# Open Xcode project
echo "Opening Xcode project..."
open CLAUDE.xcodeproj

echo ""
echo "CLAUDE Application setup complete!"
echo ""
echo "Instructions:"
echo "1. Build and run the application in Xcode"
echo "2. The backend server is running at http://localhost:8000"
echo "3. Press Ctrl+C to stop the backend server"
echo ""
echo "API Documentation available at: http://localhost:8000/docs"
echo ""
echo "Troubleshooting:"
echo "- If backend fails: Check Python dependencies and Ollama status"
echo "- If frontend fails: Ensure Xcode is properly installed"
echo ""
echo "Press Ctrl+C to stop the backend server..."

# Wait for user input to keep script running
while true; do
    sleep 1
done