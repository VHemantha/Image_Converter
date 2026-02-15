#!/bin/bash
# Quick Docker test script
# Run this after starting docker-compose to verify everything works

echo "================================"
echo "Image Converter - Docker Test"
echo "================================"
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test function
test_service() {
    local service=$1
    local test_command=$2
    local description=$3

    echo -n "Testing $description... "
    if eval "$test_command" > /dev/null 2>&1; then
        echo -e "${GREEN}✓ PASS${NC}"
        return 0
    else
        echo -e "${RED}✗ FAIL${NC}"
        return 1
    fi
}

# Check if containers are running
echo "1. Checking containers..."
test_service "redis" "docker ps | grep image_converter_redis" "Redis container"
test_service "web" "docker ps | grep image_converter_web" "Web container"
test_service "celery_worker" "docker ps | grep image_converter_celery_worker" "Celery worker"
test_service "celery_beat" "docker ps | grep image_converter_celery_beat" "Celery beat"
echo ""

# Check health endpoints
echo "2. Checking health endpoints..."
test_service "redis_ping" "docker-compose exec -T redis redis-cli ping | grep PONG" "Redis ping"
test_service "web_health" "curl -s http://localhost:5000/health | grep healthy" "Web /health"
test_service "web_ready" "curl -s http://localhost:5000/ready | grep ready" "Web /ready"
echo ""

# Check Celery
echo "3. Checking Celery..."
test_service "celery_inspect" "docker-compose exec -T celery_worker celery -A celery_worker.celery_app inspect ping" "Celery worker ping"
echo ""

# Check logs for errors
echo "4. Checking logs for errors..."
if docker-compose logs --tail=50 | grep -i "error" | grep -v "ERROR: pip's dependency"; then
    echo -e "${YELLOW}⚠ Found errors in logs (see above)${NC}"
else
    echo -e "${GREEN}✓ No errors found in recent logs${NC}"
fi
echo ""

# Summary
echo "================================"
echo "Test Summary"
echo "================================"
echo ""
echo "Services Status:"
docker-compose ps
echo ""
echo "Next Steps:"
echo "  1. Open http://localhost:5000 in your browser"
echo "  2. Upload an image and convert it"
echo "  3. Check logs: docker-compose logs -f"
echo ""
echo "Troubleshooting:"
echo "  - View logs: docker-compose logs -f [service]"
echo "  - Restart:   docker-compose restart [service]"
echo "  - Rebuild:   docker-compose up -d --build"
echo ""
