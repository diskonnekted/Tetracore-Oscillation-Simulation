#!/bin/bash

# Particle Oscillation Simulation - PHP Backend Startup Script

echo "🌌 Starting Particle Oscillation Simulation (PHP Backend)"
echo "=========================================================="

# Check if PHP is installed
if ! command -v php &> /dev/null; then
    echo "❌ PHP is not installed. Please install PHP 8.0 or higher."
    echo "   Ubuntu/Debian: sudo apt install php php-cli php-json php-mbstring"
    echo "   macOS: brew install php"
    echo "   Windows: Download from https://windows.php.net/download/"
    exit 1
fi

# Check PHP version
PHP_VERSION=$(php -r "echo phpversion();" | cut -d'.' -f1-2)
echo "✅ PHP Version: $PHP_VERSION"

# Navigate to PHP backend directory
cd /app/particle_oscillation/backend_php

# Start PHP built-in server
echo "🚀 Starting PHP built-in server on http://localhost:8003"
echo "📚 API Documentation: Check api.php endpoints"
echo ""
echo "Available endpoints:"
echo "  GET  /api.php/status"
echo "  GET  /api.php/simulation/state"
echo "  POST /api.php/simulation/start"
echo "  POST /api.php/simulation/stop"
echo "  POST /api.php/oscillators/create"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

php -S localhost:8003 -t .