#!/bin/bash

# Script to start both the Vue.js frontend and Python backend servers

case "$1" in
  start)
    echo "Starting Vue.js development server..."
    cd /home/jay.ponda/Personals/teliscript/TeliBelly
    npm run dev &
    VUE_PID=$!

    echo "Starting Python API server..."
    cd /home/jay.ponda/Personals/teliscript/TeliBelly/server
    python api_server.py &
    PYTHON_PID=$!

    echo "Servers started:"
    echo "  Vue.js frontend: http://localhost:5173 (PID: $VUE_PID)"
    echo "  Python API backend: http://localhost:5000 (PID: $PYTHON_PID)"
    echo ""
    echo "Press Ctrl+C to stop both servers"

    # Wait for both processes
    wait $VUE_PID
    wait $PYTHON_PID
    ;;
  stop)
    echo "Stopping servers..."
    pkill -f "npm run dev"
    pkill -f "api_server.py"
    echo "Servers stopped."
    ;;
  *)
    echo "Usage: $0 {start|stop}"
    exit 1
    ;;
esac