#!/bin/bash
# Start both API server and dashboard

echo "🚀 Starting Cyber Defense Simulator..."
echo ""

# Start API server in background
echo "1️⃣ Starting API server..."
python3 start_api.py > api.log 2>&1 &
API_PID=$!
echo "   API server started (PID: $API_PID)"
echo "   API available at: http://localhost:8000"
echo ""

# Wait for API to be ready
echo "⏳ Waiting for API to be ready..."
sleep 3

# Check if API is running
if curl -s http://localhost:8000/health > /dev/null; then
    echo "✅ API server is ready!"
else
    echo "⚠️  API server may not be ready yet. Continuing..."
fi

echo ""
echo "2️⃣ Starting Dashboard..."
echo "   Dashboard will be available at: http://localhost:8501"
echo ""

# Start dashboard
python3 start_dashboard.py

# Cleanup on exit
echo ""
echo "🛑 Shutting down..."
kill $API_PID 2>/dev/null
echo "✅ Done"

