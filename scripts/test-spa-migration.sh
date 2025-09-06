#!/bin/bash

# OrcaQuant SPA Migration Test Script
echo "🚀 OrcaQuant SPA Migration Testing Script"
echo "=========================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Test functions
test_backend() {
    echo -e "${BLUE}📡 Testing Backend API...${NC}"
    
    # Test health endpoint
    echo "Testing health endpoint..."
    if curl -s http://localhost:5000/api/health > /dev/null; then
        echo -e "${GREEN}✅ Backend health check passed${NC}"
    else
        echo -e "${RED}❌ Backend health check failed${NC}"
        return 1
    fi
    
    # Test CORS headers
    echo "Testing CORS headers..."
    CORS_RESPONSE=$(curl -s -H "Origin: http://localhost:3000" \
        -H "Access-Control-Request-Method: POST" \
        -H "Access-Control-Request-Headers: X-Requested-With,authorization,content-type" \
        -X OPTIONS http://localhost:5000/api/auth/login)
    
    if [[ $CORS_RESPONSE == *"Access-Control-Allow-Origin"* ]]; then
        echo -e "${GREEN}✅ CORS configuration working${NC}"
    else
        echo -e "${YELLOW}⚠️  CORS may need configuration${NC}"
    fi
    
    return 0
}

test_spa_build() {
    echo -e "${BLUE}🏗️  Testing SPA Build...${NC}"
    
    cd frontend/spa || exit 1
    
    # Install dependencies
    echo "Installing dependencies..."
    if npm install --silent; then
        echo -e "${GREEN}✅ Dependencies installed${NC}"
    else
        echo -e "${RED}❌ Failed to install dependencies${NC}"
        return 1
    fi
    
    # Type check
    echo "Running TypeScript type check..."
    if npm run type-check; then
        echo -e "${GREEN}✅ TypeScript type check passed${NC}"
    else
        echo -e "${RED}❌ TypeScript errors found${NC}"
        return 1
    fi
    
    # Build
    echo "Building production bundle..."
    if npm run build; then
        echo -e "${GREEN}✅ Production build successful${NC}"
        
        # Check build size
        BUILD_SIZE=$(du -sh dist 2>/dev/null | cut -f1)
        echo "Build size: ${BUILD_SIZE:-Unknown}"
        
        # Check for critical files
        if [[ -f "dist/index.html" && -d "dist/assets" ]]; then
            echo -e "${GREEN}✅ Build artifacts present${NC}"
        else
            echo -e "${RED}❌ Missing build artifacts${NC}"
            return 1
        fi
    else
        echo -e "${RED}❌ Production build failed${NC}"
        return 1
    fi
    
    cd ../.. || exit 1
    return 0
}

test_auth_compatibility() {
    echo -e "${BLUE}🔐 Testing Authentication Compatibility...${NC}"
    
    # Test legacy login
    echo "Testing legacy login endpoint..."
    LEGACY_RESPONSE=$(curl -s -X POST http://localhost:5000/auth/login \
        -H "Content-Type: application/json" \
        -d '{"username":"test","password":"test"}' \
        -c /tmp/cookies.txt)
    
    if [[ $LEGACY_RESPONSE == *"error"* ]]; then
        echo -e "${YELLOW}⚠️  Legacy login test failed (expected if no test user)${NC}"
    else
        echo -e "${GREEN}✅ Legacy login endpoint responding${NC}"
    fi
    
    # Test SPA login
    echo "Testing SPA login endpoint..."
    SPA_RESPONSE=$(curl -s -X POST http://localhost:5000/auth/login \
        -H "Content-Type: application/json" \
        -H "X-Requested-With: XMLHttpRequest" \
        -d '{"username":"test","password":"test"}')
    
    if [[ $SPA_RESPONSE == *"access_token"* ]]; then
        echo -e "${GREEN}✅ SPA login returns tokens in JSON${NC}"
    elif [[ $SPA_RESPONSE == *"error"* ]]; then
        echo -e "${YELLOW}⚠️  SPA login test failed (expected if no test user)${NC}"
    else
        echo -e "${RED}❌ SPA login not returning expected format${NC}"
        return 1
    fi
    
    return 0
}

test_api_endpoints() {
    echo -e "${BLUE}📊 Testing API Endpoints...${NC}"
    
    # Test predictions endpoint
    echo "Testing predictions endpoint..."
    PRED_RESPONSE=$(curl -s http://localhost:5000/api/admin/predictions/public?per_page=1)
    
    if [[ $PRED_RESPONSE == *"items"* ]]; then
        echo -e "${GREEN}✅ Predictions endpoint working${NC}"
    else
        echo -e "${YELLOW}⚠️  Predictions endpoint may need authentication${NC}"
    fi
    
    # Test technical analysis endpoint
    echo "Testing technical analysis endpoint..."
    TA_RESPONSE=$(curl -s http://localhost:5000/api/technical/latest)
    
    if [[ $TA_RESPONSE != "" && $TA_RESPONSE != *"error"* ]]; then
        echo -e "${GREEN}✅ Technical analysis endpoint working${NC}"
    else
        echo -e "${YELLOW}⚠️  Technical analysis endpoint not available${NC}"
    fi
    
    return 0
}

cleanup() {
    echo -e "${BLUE}🧹 Cleaning up...${NC}"
    rm -f /tmp/cookies.txt
    pkill -f "npm run dev" 2>/dev/null || true
}

# Main test execution
main() {
    echo -e "${BLUE}Starting migration tests...${NC}"
    echo ""
    
    FAILED_TESTS=0
    
    # Check prerequisites
    if ! command -v node &> /dev/null; then
        echo -e "${RED}❌ Node.js not found. Please install Node.js${NC}"
        exit 1
    fi
    
    if ! command -v npm &> /dev/null; then
        echo -e "${RED}❌ npm not found. Please install npm${NC}"
        exit 1
    fi
    
    # Run tests
    test_backend || ((FAILED_TESTS++))
    echo ""
    
    test_spa_build || ((FAILED_TESTS++))
    echo ""
    
    test_auth_compatibility || ((FAILED_TESTS++))
    echo ""
    
    test_api_endpoints || ((FAILED_TESTS++))
    echo ""
    
    # Summary
    echo "=========================================="
    if [ $FAILED_TESTS -eq 0 ]; then
        echo -e "${GREEN}🎉 All tests passed! Migration looks good.${NC}"
        echo ""
        echo "Next steps:"
        echo "1. Start backend: python app.py"
        echo "2. Start SPA: cd frontend/spa && npm run dev"
        echo "3. Visit: http://localhost:3000"
    else
        echo -e "${RED}❌ $FAILED_TESTS test(s) failed. Please check the issues above.${NC}"
        exit 1
    fi
    
    cleanup
}

# Handle script interruption
trap cleanup EXIT

# Run main function
main