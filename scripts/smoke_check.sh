#!/bin/bash

set -e

echo "🚀 Starting CarePath AI services with Docker Compose..."
docker compose up --build -d

echo "⏳ Waiting for services to be ready..."
sleep 10

# Function to check health endpoint
check_health() {
    local service_name=$1
    local port=$2
    local max_attempts=30
    local attempt=1
    
    echo "🔍 Checking $service_name health on port $port..."
    
    while [ $attempt -le $max_attempts ]; do
        if curl -s "http://localhost:$port/health" | grep -q "ok"; then
            echo "✅ $service_name is healthy!"
            return 0
        fi
        
        echo "⏳ Attempt $attempt/$max_attempts: $service_name not ready yet..."
        sleep 2
        ((attempt++))
    done
    
    echo "❌ $service_name failed to become healthy after $max_attempts attempts"
    return 1
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
echo "📊 Detailed health check results:"
echo "=================================="

# Detailed health checks with response output
echo "🔍 API Health Check (http://localhost:5000/health):"
if curl -s "http://localhost:5000/health"; then
    echo ""
else
    echo "❌ API health check failed"
fi

echo ""
echo "🔍 ML Health Check (http://localhost:8000/health):"
if curl -s "http://localhost:8000/health"; then
    echo ""
else
    echo "❌ ML health check failed"
fi

echo ""
echo "🔍 UI Health Check (http://localhost:5001/health):"
if curl -s "http://localhost:5001/health"; then
    echo ""
else
    echo "❌ UI health check failed"
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