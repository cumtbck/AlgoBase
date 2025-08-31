#!/bin/bash

# CLAUDE Application Launcher

echo "Starting CLAUDE Application..."

# Check if we're in the right directory
if [ ! -f "CLAUDE/README.md" ]; then
    echo "Error: Please run this script from the root directory containing CLAUDE/"
    exit 1
fi

# Function to cleanup background processes
cleanup() {
    echo "Shutting down CLAUDE..."
    if [ ! -z "$BACKEND_PID" ]; then
        kill $BACKEND_PID 2>/dev/null
    fi
    exit 0
}

# Set up signal handlers
trap cleanup SIGINT SIGTERM

# Start backend server
echo "Starting backend server..."
cd CLAUDE/backend

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
else
    source venv/bin/activate
fi

# Copy environment file if it doesn't exist
if [ ! -f ".env" ]; then
    cp .env.example .env
    echo "Environment file created. Please edit .env if needed."
fi

# Start backend in background
python main.py &
BACKEND_PID=$!

# Wait a moment for backend to start
sleep 3

# Check if backend is running
if ! curl -s http://localhost:8000/health > /dev/null; then
    echo "Error: Backend server failed to start"
    kill $BACKEND_PID 2>/dev/null
    exit 1
fi

echo "Backend server started successfully (PID: $BACKEND_PID)"
echo "API available at: http://localhost:8000"

# Start frontend application
echo "Starting frontend application..."
cd ../frontend

# Check if Xcode project exists
if [ ! -f "CLAUDE.xcodeproj/project.pbxproj" ]; then
    echo "Error: Xcode project not found"
    kill $BACKEND_PID 2>/dev/null
    exit 1
fi

# Open Xcode project
open CLAUDE.xcodeproj

echo ""
echo "CLAUDE Application started successfully!"
echo ""
echo "Instructions:"
echo "1. Build and run the application in Xcode"
echo "2. The backend server is already running at http://localhost:8000"
echo "3. Press Ctrl+C to stop the backend server"
echo ""
echo "API Documentation available at: http://localhost:8000/docs"
echo ""

# Wait for user input to keep script running
echo "Press Ctrl+C to stop the backend server..."
while true; do
    sleep 1
done