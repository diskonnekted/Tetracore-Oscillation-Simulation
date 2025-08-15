#!/bin/bash

# Particle Oscillation Simulation - Python Backend Startup Script

echo "🌌 Starting Particle Oscillation Simulation (Python Backend)"
echo "============================================================="

# Navigate to Python backend directory
cd /app/particle_oscillation/backend_python

# Activate virtual environment
echo "📦 Activating virtual environment..."
source venv/bin/activate

# Check if dependencies are installed
if [ ! -f "venv/lib/python*/site-packages/fastapi/__init__.py" ]; then
    echo "📥 Installing Python dependencies..."
    pip install -r requirements.txt
fi

# Set environment variables
export PYTHONPATH="${PYTHONPATH}:/app/particle_oscillation/backend_python"

# Start the FastAPI server
echo "🚀 Starting FastAPI server on http://localhost:8002"
echo "📡 WebSocket available at ws://localhost:8002/api/ws"
echo "📚 API Documentation: http://localhost:8002/docs"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

python api_server.py