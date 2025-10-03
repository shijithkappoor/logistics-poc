#!/bin/bash

# Start the server in the background
cd /Users/shijithk/Desktop/poc/logistics
.venv/bin/uvicorn main:app --port 8003 &
SERVER_PID=$!

# Wait for server to start
sleep 3

echo "🚛 Testing Routing API Endpoints"
echo "=================================================="

# Test health endpoint
echo "Testing health endpoint..."
curl -s http://localhost:8003/health | json_pp
echo

# Test plan/run endpoint
echo "Testing POST /routing/plan/run..."
curl -s -X POST http://localhost:8003/routing/plan/run \
  -H "Content-Type: application/json" \
  -d '{
    "for_date": "2024-12-15",
    "depots": [
      {
        "id": "depot_north",
        "location": {"lat": 43.761539, "lon": -79.411079}
      }
    ],
    "trucks": [
      {
        "id": "truck_001",
        "depot_id": "depot_north",
        "capacity_cuft": 1000
      }
    ],
    "stops": [
      {
        "order_id": "ORD001",
        "franchisee_id": "FRAN001",
        "location": {"lat": 43.7165, "lon": -79.3404},
        "items_volume_cuft": 150,
        "service_min": 20
      },
      {
        "order_id": "ORD002", 
        "franchisee_id": "FRAN002",
        "location": {"lat": 43.6426, "lon": -79.3871},
        "items_volume_cuft": 200,
        "service_min": 25
      }
    ]
  }' | json_pp

echo 
echo "Testing routing health endpoint..."
curl -s http://localhost:8003/routing/health | json_pp

# Clean up
echo
echo "Stopping server..."
kill $SERVER_PID
wait $SERVER_PID 2>/dev/null

echo "✨ Testing completed!"