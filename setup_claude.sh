#!/bin/bash

# CLAUDE Manual Setup Script

echo "CLAUDE Manual Setup"
echo "=================="

# Find the CLAUDE directory
if [ -f "CLAUDE/README.md" ]; then
    CLAUDE_DIR="CLAUDE"
elif [ -f "README.md" ] && [ -f "start.sh" ]; then
    CLAUDE_DIR="."
else
    echo "Error: Cannot find CLAUDE directory."
    exit 1
fi

echo "Using CLAUDE directory: $CLAUDE_DIR"

cd "$CLAUDE_DIR/backend"

echo ""
echo "1. Setting up Python environment..."

# Check if conda is available
if command -v conda &> /dev/null; then
    echo "Using conda for environment management..."
    CONDA_ENV_NAME="claude_env"
    
    if ! conda env list | grep -q "^$CONDA_ENV_NAME\s"; then
        echo "Creating conda environment: $CONDA_ENV_NAME"
        conda create -n $CONDA_ENV_NAME python=3.10 -y
    fi
    
    echo "Activating conda environment..."
    source "$(conda info --base)/etc/profile.d/conda.sh"
    conda activate $CONDA_ENV_NAME
else
    echo "Conda not found, using venv..."
    if [ ! -d "venv" ]; then
        echo "Creating virtual environment..."
        python3 -m venv venv
    fi
    echo "Activating virtual environment..."
    source venv/bin/activate
fi

echo ""
echo "2. Installing dependencies..."

# Upgrade pip
pip install --upgrade pip

# Install dependencies
echo "Installing Python packages..."
pip install -r requirements.txt

echo ""
echo "3. Setting up environment file..."

if [ ! -f ".env" ]; then
    cp .env.example .env
    echo "Environment file created: .env"
    echo "You may want to edit this file for custom settings."
fi

echo ""
echo "4. Checking Ollama installation..."

if command -v ollama &> /dev/null; then
    echo "✓ Ollama is installed"
    
    if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
        echo "✓ Ollama is running"
        
        # Check if CodeLlama is available
        if ollama list | grep -q "codellama:7b"; then
            echo "✓ CodeLlama 7B model is available"
        else
            echo "⚠ CodeLlama 7B model not found. You can download it with:"
            echo "  ollama pull codellama:7b"
        fi
    else
        echo "⚠ Ollama is not running. Start it with:"
        echo "  ollama serve"
    fi
else
    echo "⚠ Ollama is not installed. Install it with:"
    echo "  brew install ollama"
fi

echo ""
echo "5. Testing backend server..."

# Test if backend can start
echo "Testing backend startup..."
timeout 10s python main.py &
BACKEND_TEST_PID=$!

sleep 3

if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "✓ Backend server started successfully"
    kill $BACKEND_TEST_PID 2>/dev/null
else
    echo "⚠ Backend server test failed. Check for errors above."
    kill $BACKEND_TEST_PID 2>/dev/null
fi

echo ""
echo "Setup complete!"
echo ""
echo "To start CLAUDE:"
echo "1. Start backend: cd $CLAUDE_DIR/backend && source venv/bin/activate && python main.py"
echo "2. Start frontend: cd $CLAUDE_DIR/frontend && open CLAUDE.xcodeproj"
echo ""
echo "Or use the automated script: ./start_claude_conda.sh"