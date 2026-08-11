#!/bin/bash
# TruthLens — One-click startup script (Linux/Mac)

echo ""
echo "  🔍 TruthLens — Fake News Detector"
echo "  Starting all services..."
echo ""

# Start backend
echo "  [1/2] Starting Backend (FastAPI)..."
cd backend && uvicorn main:app --reload --port 8000 &
BACKEND_PID=$!
cd ..

# Wait for backend to start
sleep 3

# Start frontend
echo "  [2/2] Starting Frontend..."
cd frontend && python3 -m http.server 5000 &
FRONTEND_PID=$!
cd ..

sleep 1
echo ""
echo "  ✅ Backend  → http://127.0.0.1:8000"
echo "  ✅ Frontend → http://localhost:5000"
echo ""

# Open browser
if command -v xdg-open &> /dev/null; then
    xdg-open http://localhost:5000
elif command -v open &> /dev/null; then
    open http://localhost:5000
fi

echo "  Press Ctrl+C to stop all servers."
echo ""

# Wait and cleanup on exit
trap "kill $BACKEND_PID $FRONTEND_PID; echo 'Servers stopped.'; exit" INT
wait
