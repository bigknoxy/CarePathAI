#!/bin/bash

echo "🚀 Simple smoke check for CarePath AI..."

# Function to check health endpoint
check_health() {
    local service_name=$1
    local port=$2
    
    echo "🔍 Checking $service_name health on port $port..."
    
    if curl -s "http://localhost:$port/health" | grep -q "ok"; then
        echo "✅ $service_name is healthy!"
        return 0
    else
        echo "❌ $service_name health check failed"
        return 1
    fi
}

# Check all health endpoints
services_passed=0
total_services=3

if check_health "API" 5000; then
    ((services_passed++))
fi

if check_health "ML" 8000; then
    ((services_passed++))
fi

if check_health "UI" 5001; then
    ((services_passed++))
fi

echo ""
echo "🐳 Docker Compose Status:"
docker compose ps

echo ""
echo "📈 Health Check Summary: $services_passed/$total_services services passed"

if [ $services_passed -eq $total_services ]; then
    echo "🎉 All services are healthy!"
    exit 0
else
    echo "💥 Some services failed health checks!"
    exit 1
fi