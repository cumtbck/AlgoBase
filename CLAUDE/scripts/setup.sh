#!/bin/bash

# CLAUDE Development Setup Script

echo "Setting up CLAUDE development environment..."

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt

# Create necessary directories
mkdir -p data/vector_db
mkdir -p data/finetuning
mkdir -p data/adapters
mkdir -p logs

# Copy environment file
cp .env.example .env

echo "Setup complete!"
echo "Activate virtual environment with: source venv/bin/activate"
echo "Start the backend server with: python -m api.server"