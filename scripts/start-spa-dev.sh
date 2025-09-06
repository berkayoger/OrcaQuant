#!/bin/bash

# OrcaQuant SPA Development Starter Script
echo "🚀 Starting OrcaQuant SPA Development Environment"
echo "================================================="

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Check if backend is running
check_backend() {
    echo -e "${BLUE}🔍 Checking backend status...${NC}"
    
    if curl -s http://localhost:5000/api/health > /dev/null; then
        echo -e "${GREEN}✅ Backend is running on http://localhost:5000${NC}"
        return 0
    else
        echo -e "${YELLOW}⚠️  Backend not detected on http://localhost:5000${NC}"
        echo "Please start the backend first:"
        echo "  cd /workspaces/ytd-kopya"
        echo "  python app.py"
        echo ""
        read -p "Continue anyway? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            echo "Exiting..."
            exit 1
        fi
        return 1
    fi
}

# Install dependencies if needed
setup_spa() {
    echo -e "${BLUE}📦 Setting up SPA...${NC}"
    
    cd frontend/spa || {
        echo -e "${RED}❌ SPA directory not found${NC}"
        exit 1
    }
    
    if [[ ! -d "node_modules" ]]; then
        echo "Installing dependencies..."
        npm install || {
            echo -e "${RED}❌ Failed to install dependencies${NC}"
            exit 1
        }
        echo -e "${GREEN}✅ Dependencies installed${NC}"
    else
        echo -e "${GREEN}✅ Dependencies already installed${NC}"
    fi
    
    # Create .env if it doesn't exist
    if [[ ! -f ".env" ]]; then
        cp .env.example .env
        echo -e "${GREEN}✅ Created .env file${NC}"
    fi
}

# Start development server
start_dev_server() {
    echo -e "${BLUE}🚀 Starting development server...${NC}"
    echo ""
    echo -e "${GREEN}📱 SPA will be available at: http://localhost:3000${NC}"
    echo -e "${GREEN}🔗 API proxied from: http://localhost:5000${NC}"
    echo ""
    echo "Press Ctrl+C to stop the development server"
    echo ""
    
    # Start Vite dev server
    npm run dev
}

# Cleanup function
cleanup() {
    echo ""
    echo -e "${BLUE}🧹 Shutting down development server...${NC}"
    pkill -f "vite" 2>/dev/null || true
    echo -e "${GREEN}✅ Development server stopped${NC}"
}

# Main function
main() {
    # Check prerequisites
    if ! command -v node &> /dev/null; then
        echo -e "${RED}❌ Node.js not found. Please install Node.js 18+${NC}"
        exit 1
    fi
    
    if ! command -v npm &> /dev/null; then
        echo -e "${RED}❌ npm not found. Please install npm${NC}"
        exit 1
    fi
    
    # Show Node.js version
    NODE_VERSION=$(node --version)
    echo -e "${BLUE}📋 Using Node.js ${NODE_VERSION}${NC}"
    
    # Check backend
    check_backend
    
    # Setup SPA
    setup_spa
    
    # Start development server
    start_dev_server
}

# Handle interruption
trap cleanup EXIT

# Run main function
main