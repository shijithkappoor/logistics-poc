#!/bin/bash

# Start the server in the background
cd /Users/shijithk/Desktop/poc/logistics
.venv/bin/uvicorn main:app --port 8003 &
SERVER_PID=$!

# Wait for server to start
sleep 3

echo "🚛 Testing Reroute Endpoint"
echo "=================================================="

# First create a plan
echo "Step 1: Creating initial plan..."
PLAN_RESPONSE=$(curl -s -X POST http://localhost:8003/routing/plan/run \
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
      },
      {
        "id": "truck_002",
        "depot_id": "depot_north",
        "capacity_cuft": 1200
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
      },
      {
        "order_id": "ORD003",
        "franchisee_id": "FRAN003",
        "location": {"lat": 43.6532, "lon": -79.3832},
        "items_volume_cuft": 100,
        "service_min": 15
      },
      {
        "order_id": "ORD004",
        "franchisee_id": "FRAN004",
        "location": {"lat": 43.7001, "lon": -79.4163},
        "items_volume_cuft": 300,
        "service_min": 30
      }
    ]
  }')

PLAN_ID=$(echo $PLAN_RESPONSE | python3 -c "import sys, json; print(json.load(sys.stdin)['plan_id'])")
echo "Created plan: $PLAN_ID"

echo
echo "Step 2: Testing global reroute..."
curl -s -X POST http://localhost:8003/routing/reroute \
  -H "Content-Type: application/json" \
  -d "{
    \"plan_id\": \"$PLAN_ID\",
    \"scope\": \"global\",
    \"change_limit\": 0.3,
    \"lock_hops\": 2,
    \"reason\": \"incident\"
  }" | json_pp

echo
echo "Step 3: Testing truck-specific reroute..."
curl -s -X POST http://localhost:8003/routing/reroute \
  -H "Content-Type: application/json" \
  -d "{
    \"plan_id\": \"$PLAN_ID\",
    \"scope\": \"truck\",
    \"truck_id\": \"truck_001\",
    \"change_limit\": 0.2,
    \"lock_hops\": 1,
    \"reason\": \"eta_risk\"
  }" | json_pp

# Test validation error (missing truck_id)
echo
echo "Step 4: Testing validation (should fail)..."
curl -s -X POST http://localhost:8003/routing/reroute \
  -H "Content-Type: application/json" \
  -d "{
    \"plan_id\": \"$PLAN_ID\",
    \"scope\": \"truck\",
    \"change_limit\": 0.2,
    \"lock_hops\": 1,
    \"reason\": \"eta_risk\"
  }" | json_pp

# Clean up
echo
echo "Stopping server..."
kill $SERVER_PID
wait $SERVER_PID 2>/dev/null

echo "✨ Reroute testing completed!"