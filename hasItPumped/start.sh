#!/bin/bash

# Start backend
cd backend
echo "Starting FastAPI backend..."
eval $(poetry env activate)
python ./run.py & 
BACKEND_PID=$!

# Start frontend
cd ../frontend
echo "Starting Next.js frontend..."
npm run dev &
FRONTEND_PID=$!

# Function to kill processes on exit
function cleanup {
    echo "Stopping services..."
    kill $BACKEND_PID
    kill $FRONTEND_PID
}

# Register the cleanup function for SIGINT
trap cleanup SIGINT

echo "Services started!"
echo "Backend: http://localhost:8000"
echo "Frontend: http://localhost:3000"
echo "Press Ctrl+C to stop all services"

# Wait for processes
wait
