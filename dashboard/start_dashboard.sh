#!/bin/bash
#
# Quick Start Script for 5G-IoT Anomaly Detection Dashboard
# This script helps you quickly start the dashboard system
#

echo "============================================================"
echo "5G-IoT Anomaly Detection Dashboard - Quick Start"
echo "============================================================"
echo ""

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo -e "${YELLOW}Warning: python3 not found. Please install Python 3.7 or higher.${NC}"
    exit 1
fi

echo -e "${GREEN}✓${NC} Python found: $(python3 --version)"
echo ""

# Install dependencies
echo -e "${BLUE}Step 1: Installing dependencies...${NC}"
pip install -q -r requirements.txt
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓${NC} Dependencies installed successfully"
else
    echo -e "${YELLOW}Warning: Failed to install some dependencies${NC}"
fi
echo ""

# Check if port 5000 is available
if lsof -Pi :5000 -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo -e "${YELLOW}Warning: Port 5000 is already in use${NC}"
    echo "You may need to stop the existing process or change the port."
    echo ""
fi

# Ask user what to do
echo "What would you like to do?"
echo "  1) Start Backend Server only"
echo "  2) Start Backend Server + Test Data Generator"
echo "  3) Start Backend Server + Open Frontend"
echo "  4) Full Setup (Backend + Frontend + Test Data)"
echo ""
read -p "Enter choice [1-4]: " choice

case $choice in
    1)
        echo ""
        echo -e "${BLUE}Starting Backend Server...${NC}"
        echo "Access API at: http://localhost:5000"
        echo "Press Ctrl+C to stop"
        echo ""
        cd backend && python3 app.py
        ;;
    2)
        echo ""
        echo -e "${BLUE}Starting Backend Server and Test Data Generator...${NC}"
        echo ""
        # Start backend in background
        cd backend && python3 app.py &
        BACKEND_PID=$!
        sleep 3
        
        # Start test data generator
        echo ""
        echo -e "${BLUE}Starting Test Data Generator...${NC}"
        echo "Press Ctrl+C to stop"
        echo ""
        cd ..
        python3 test_dashboard.py
        
        # Cleanup
        kill $BACKEND_PID 2>/dev/null
        ;;
    3)
        echo ""
        echo -e "${BLUE}Starting Backend Server...${NC}"
        cd backend && python3 app.py &
        BACKEND_PID=$!
        sleep 3
        
        echo ""
        echo -e "${GREEN}✓${NC} Backend started (PID: $BACKEND_PID)"
        echo ""
        echo -e "${BLUE}Opening Frontend...${NC}"
        
        # Try to open frontend based on OS
        if command -v xdg-open &> /dev/null; then
            xdg-open ../frontend/index.html
        elif command -v open &> /dev/null; then
            open ../frontend/index.html
        else
            echo "Please manually open: $(pwd)/../frontend/index.html"
        fi
        
        echo ""
        echo "Dashboard is running!"
        echo "Backend: http://localhost:5000"
        echo "Frontend: file://$(pwd)/../frontend/index.html"
        echo ""
        echo "Press Enter to stop the backend server..."
        read
        
        kill $BACKEND_PID 2>/dev/null
        echo -e "${GREEN}✓${NC} Backend stopped"
        ;;
    4)
        echo ""
        echo -e "${BLUE}Full Setup - Starting all components...${NC}"
        echo ""
        
        # Start backend in background
        cd backend && python3 app.py &
        BACKEND_PID=$!
        sleep 3
        echo -e "${GREEN}✓${NC} Backend started"
        
        # Open frontend
        cd ..
        if command -v xdg-open &> /dev/null; then
            xdg-open frontend/index.html &
        elif command -v open &> /dev/null; then
            open frontend/index.html &
        else
            echo "Please manually open: $(pwd)/frontend/index.html"
        fi
        echo -e "${GREEN}✓${NC} Frontend opened"
        
        # Start test data generator
        sleep 2
        echo ""
        echo -e "${BLUE}Starting Test Data Generator...${NC}"
        echo "Press Ctrl+C to stop all components"
        echo ""
        python3 test_dashboard.py
        
        # Cleanup
        kill $BACKEND_PID 2>/dev/null
        echo ""
        echo -e "${GREEN}✓${NC} All components stopped"
        ;;
    *)
        echo "Invalid choice. Exiting."
        exit 1
        ;;
esac

echo ""
echo "============================================================"
echo "Thank you for using the 5G-IoT Anomaly Detection Dashboard!"
echo "============================================================"
