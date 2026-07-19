#!/bin/bash
# NetElixIQ AI — Development Server Launcher
# Starts both FastAPI backend and Vite frontend dev servers.
# Run from the project root directory.

echo -e "\e[36mNetElixIQ AI — Starting Development Servers...\e[0m"
echo -e "\e[36m=============================================\e[0m"

# Start Backend
echo -e "\n\e[33m[1/2] Starting FastAPI Backend (port 8000)...\e[0m"
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!

# Wait for backend to boot
sleep 3

# Start Frontend
echo -e "\e[33m[2/2] Starting Vite Frontend (port 3000)...\e[0m"
cd frontend
npm run dev &
FRONTEND_PID=$!
cd ..

echo -e "\n\e[32m=============================================\e[0m"
echo -e "\e[32mNetElixIQ AI is running!\e[0m"
echo -e "  Frontend: http://localhost:3000"
echo -e "  Backend:  http://localhost:8000"
echo -e "  API Docs: http://localhost:8000/api/docs"
echo -e "\e[32m=============================================\e[0m"
echo "Press Ctrl+C to stop both processes."

cleanup() {
    echo -e "\n\e[31mStopping servers (PID $BACKEND_PID, $FRONTEND_PID)...\e[0m"
    kill $BACKEND_PID 2>/dev/null
    kill $FRONTEND_PID 2>/dev/null
    exit 0
}

trap cleanup SIGINT SIGTERM
wait
