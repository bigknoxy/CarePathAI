#!/bin/bash
# Rebuild and test ML service

echo "🔨 Building ML service container..."
cd /home/josh/projects/CarePathAI
docker-compose build carepath_ml

echo "🚀 Starting ML service..."
docker-compose up -d carepath_ml

echo "⏳ Waiting for service to be ready..."
sleep 10

echo "🧪 Running retrieval tests..."
cd carepath_ml
python test_retrieval.py --mode http

echo "📊 Testing with curl example..."
curl -X POST "http://localhost:8000/retrieve" \
  -H "Content-Type: application/json" \
  -d '{"query": "diabetes medication", "top_k": 3}' | jq .

echo "✅ Testing complete!"