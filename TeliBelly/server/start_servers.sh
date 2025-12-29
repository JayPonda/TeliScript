#!/bin/bash

# Script to start both the main API server and the Telegram scraper API

echo "🚀 Starting Telegram Messages Dashboard API..."
cd /home/jay.ponda/Personals/teliscript/TeliBelly/server

# Start the main API server in the background
echo "Starting main API server on port 5000..."
python api_server.py &
MAIN_PID=$!

# Start the Telegram scraper API in the background
echo "Starting Telegram scraper API on port 5001..."
python telegram_scraper_api.py &
SCRAPER_PID=$!

echo "✅ Both servers started!"
echo "   Main API: http://localhost:5000"
echo "   Scraper API: http://localhost:5001"
echo "Press Ctrl+C to stop both servers"

# Wait for both processes
wait $MAIN_PID
wait $SCRAPER_PID

echo "🛑 Servers stopped"