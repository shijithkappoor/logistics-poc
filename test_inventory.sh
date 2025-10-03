#!/bin/bash

BASE_URL="http://localhost:8004"

echo "📦 Testing Inventory API Endpoints"
echo "=================================================="

# Test health endpoint
echo "Step 1: Testing inventory health..."
curl -s $BASE_URL/inventory/health | json_pp
echo

# Test snapshot endpoint
echo "Step 2: Testing GET /inventory/snapshot..."
curl -s "$BASE_URL/inventory/snapshot?location_type=warehouse&location_id=WH_NORTH&item_ids=BREAD_WHITE&item_ids=MILK_2PCT" | json_pp
echo

# Test feasibility check
echo "Step 3: Testing POST /inventory/feasibility..."
curl -s -X POST $BASE_URL/inventory/feasibility \
  -H "Content-Type: application/json" \
  -d '{
    "lines": [
      {
        "order_id": "ORD001",
        "warehouse_id": "WH_NORTH",
        "item_id": "BREAD_WHITE",
        "qty": 50,
        "non_substitutable": false
      },
      {
        "order_id": "ORD002",
        "warehouse_id": "WH_NORTH",
        "item_id": "MILK_2PCT",
        "qty": 25,
        "non_substitutable": true
      },
      {
        "order_id": "ORD003",
        "warehouse_id": "WH_NORTH",
        "item_id": "RARE_ITEM_999",
        "qty": 100,
        "non_substitutable": true
      }
    ]
  }' | json_pp
echo

# Test reservation
echo "Step 4: Testing POST /inventory/reserve..."
RESERVE_RESPONSE=$(curl -s -X POST $BASE_URL/inventory/reserve \
  -H "Content-Type: application/json" \
  -d '{
    "plan_id": "plan_001",
    "ttl_minutes": 60,
    "lines": [
      {
        "warehouse_id": "WH_NORTH",
        "order_id": "ORD001",
        "item_id": "BREAD_WHITE",
        "qty": 30,
        "non_substitutable": false
      },
      {
        "warehouse_id": "WH_NORTH",
        "order_id": "ORD002",
        "item_id": "MILK_2PCT",
        "qty": 20,
        "non_substitutable": true
      }
    ]
  }')

echo $RESERVE_RESPONSE | json_pp
echo

# Extract reservation IDs for testing release
RESERVATION_IDS=$(echo $RESERVE_RESPONSE | python3 -c "
import sys, json
data = json.load(sys.stdin)
ids = [res['reservation_id'] for res in data.get('reservations', [])]
print(json.dumps(ids))
")

echo "Reserved IDs: $RESERVATION_IDS"
echo

# Test stock events
echo "Step 5: Testing POST /inventory/events..."
curl -s -X POST $BASE_URL/inventory/events \
  -H "Content-Type: application/json" \
  -d '[
    {
      "id": "event_001",
      "type": "replenish",
      "ts": "2024-12-15T10:00:00Z",
      "warehouse_id": "WH_NORTH",
      "item_id": "BREAD_WHITE",
      "qty": 100,
      "reason": "morning_delivery"
    },
    {
      "id": "event_002",
      "type": "transfer",
      "ts": "2024-12-15T11:00:00Z",
      "from_warehouse_id": "WH_NORTH",
      "to_warehouse_id": "WH_WEST",
      "item_id": "MILK_2PCT",
      "qty": 50,
      "reason": "rebalancing"
    },
    {
      "id": "event_003",
      "type": "consume",
      "ts": "2024-12-15T12:00:00Z",
      "franchisee_id": "FRAN_001",
      "item_id": "EGGS_DOZEN",
      "qty": 5,
      "reason": "customer_purchase"
    }
  ]' | json_pp
echo

# Test snapshot with reservations after events
echo "Step 6: Testing snapshot with reservations..."
curl -s "$BASE_URL/inventory/snapshot?location_type=warehouse&location_id=WH_NORTH&include_reservations=true" | json_pp | head -50
echo

# Test release reservations
echo "Step 7: Testing POST /inventory/release..."
curl -s -X POST $BASE_URL/inventory/release \
  -H "Content-Type: application/json" \
  -d "{
    \"plan_id\": \"plan_001\"
  }" | json_pp
echo

# Test metrics
echo "Step 8: Testing inventory metrics..."
curl -s $BASE_URL/inventory/metrics | json_pp
echo

echo "✨ Inventory API testing completed!"