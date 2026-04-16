#!/bin/bash
# Start the extraction web app and open in browser

cd "$(dirname "$0")/web"

echo "Starting Portfolio Extraction server..."
echo "Opening http://localhost:8000"
echo ""

# Open browser after a short delay
(sleep 1 && open http://localhost:8000) &

# Start server (blocks until Ctrl+C)
uvicorn app:app --port 8000
