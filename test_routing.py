"""
Test script for routing API endpoints
"""
import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:8003"

def test_plan_run():
    """Test the /routing/plan/run endpoint"""
    print("Testing POST /routing/plan/run...")
    
    request_data = {
        "for_date": "2024-12-15",
        "depots": [
            {
                "id": "depot_north",
                "location": {"lat": 43.761539, "lon": -79.411079}
            },
            {
                "id": "depot_west", 
                "location": {"lat": 43.650570, "lon": -79.547849}
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
                "depot_id": "depot_west",
                "capacity_cuft": 1200
            },
            {
                "id": "truck_003",
                "depot_id": "depot_north", 
                "capacity_cuft": 800
            }
        ],
        "stops": [
            {
                "order_id": "ORD001",
                "franchisee_id": "FRAN001",
                "location": {"lat": 43.7165, "lon": -79.3404},
                "items_volume_cuft": 150,
                "service_min": 20,
                "window_start": "06:00",
                "window_end": "10:00"
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
            },
            {
                "order_id": "ORD005",
                "franchisee_id": "FRAN005",
                "location": {"lat": 43.6818, "lon": -79.6304},
                "items_volume_cuft": 250,
                "service_min": 20
            },
            {
                "order_id": "ORD006",
                "franchisee_id": "FRAN006",
                "location": {"lat": 43.7280, "lon": -79.1693},
                "items_volume_cuft": 180,
                "service_min": 22
            }
        ],
        "params": {
            "overlap_h3_res": 8,
            "avoid_overlap_weight": 1.5,
            "unused_truck_weight": 0.2
        },
        "traffic_profile_id": "current_traffic"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/routing/plan/run", json=request_data)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Plan created: {data['plan_id']}")
            print(f"Runtime: {data['runtime_s']:.2f}s")
            print(f"Routes: {len(data['routes'])}")
            print(f"Overlap incidents: {len(data['overlap_incidents'])}")
            print(f"KPIs: on_time={data['kpi']['on_time_pct']:.1%}, overlap={data['kpi']['overlap_pct']:.1%}, miles/order={data['kpi']['miles_per_order']:.1f}")
            
            # Verify H3 population
            h3_populated = 0
            total_stops = 0
            for route in data['routes']:
                for stop in route['stops']:
                    total_stops += 1
                    if stop.get('h3'):
                        h3_populated += 1
            print(f"H3 cells populated: {h3_populated}/{total_stops} stops")
            
            # Verify utilization calculations
            print("\nRoute Details:")
            for route in data['routes']:
                delivery_volume = sum(stop['load_cuft'] for stop in route['stops'] if stop['type'] == 'delivery')
                print(f"  Truck {route['truck_id']}: {route['utilization_pct']:.1%} utilization, {delivery_volume:.0f} cuft loaded")
            
            # Verify loading order (reverse delivery sequence)
            print("\nPick/Pack Details:")
            for pp in data['pickpack']:
                print(f"  Truck {pp['truck_id']}: {len(pp['pick_sequence'])} pick tasks, loading order: {pp['loading_order']}")
            
            return data['plan_id']
        else:
            print(f"❌ Error: {response.text}")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
        return None


def test_reroute(plan_id):
    """Test the /routing/reroute endpoint"""
    if not plan_id:
        print("⏭️  Skipping reroute test - no plan_id available")
        return
        
    print(f"\nTesting POST /routing/reroute with plan {plan_id}...")
    
    request_data = {
        "plan_id": plan_id,
        "scope": "global",
        "change_limit": 0.3,
        "lock_hops": 2,
        "reason": "incident",
        "params": {
            "max_change_ratio": 0.3
        }
    }
    
    try:
        response = requests.post(f"{BASE_URL}/routing/reroute", json=request_data)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Re-routing completed for plan: {data['plan_id']}")
            print(f"Changed stops: {data['changed_stops_pct']:.1%}")
            print(f"Runtime: {data['runtime_s']:.2f}s")
            print(f"Updated KPIs: on_time={data['kpi']['on_time_pct']:.1%}, overlap={data['kpi']['overlap_pct']:.1%}")
            return True
        else:
            print(f"❌ Error: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
        return False


def test_truck_specific_reroute(plan_id):
    """Test truck-specific reroute"""
    if not plan_id:
        print("⏭️  Skipping truck reroute test - no plan_id available")
        return
        
    print(f"\nTesting POST /routing/reroute with truck scope...")
    
    request_data = {
        "plan_id": plan_id,
        "scope": "truck",
        "truck_id": "truck_001",
        "change_limit": 0.2,
        "lock_hops": 1,
        "reason": "eta_risk"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/routing/reroute", json=request_data)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Truck-specific re-routing completed")
            print(f"Changed stops: {data['changed_stops_pct']:.1%}")
            print(f"Runtime: {data['runtime_s']:.2f}s")
            return True
        else:
            print(f"❌ Error: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
        return False


def test_health():
    """Test health endpoints"""
    print("\nTesting health endpoints...")
    
    try:
        # Test main health
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code == 200:
            print("✅ Main health check passed")
        
        # Test routing health
        response = requests.get(f"{BASE_URL}/routing/health")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Routing health check passed - H3 available: {data.get('h3_available', False)}")
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Health check failed: {e}")


if __name__ == "__main__":
    print("🚛 Testing Routing API Endpoints")
    print("=" * 50)
    
    # Test health first
    test_health()
    
    # Test plan run
    plan_id = test_plan_run()
    
    # Test rerouting
    test_reroute(plan_id)
    test_truck_specific_reroute(plan_id)
    
    print("\n" + "=" * 50)
    print("✨ Testing completed!")