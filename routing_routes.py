"""
FastAPI router for routing endpoints
"""
from fastapi import APIRouter, HTTPException, status
from routing_models import PlanRunRequest, ReRouteRequest, PlanRunResponse, ReRouteResponse
from routing_simulator import RoutingSimulator
from routing_models import OrderStop, Depot, TruckSpec, Location, RoutingParams
import random
import logging
import requests
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from seed_mcdonalds_inventory import get_db_connection

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/routing", tags=["routing"])

# Initialize simulator
simulator = RoutingSimulator()

# Simple in-memory live positions simulator (advances when polled)
_live_positions: Dict[str, Dict[str, Any]] = {}

def _init_live_positions_if_needed():
    # Seed from a simple vehicle fleet or known trucks
    global _live_positions
    if _live_positions:
        return

    # If we have a planned route cached with geometries, seed positions from that
    try:
        if getattr(simulator, '_plan_cache', None):
            plans = list(simulator._plan_cache.values())
            if plans:
                last_plan = plans[-1]
                # last_plan may be OptimizationResult with route_geometries
                geoms = getattr(last_plan, 'route_geometries', {}) or {}
                for truck_id, geom in geoms.items():
                    if geom and len(geom) > 0:
                        # geom is list of [lon, lat]
                        lon, lat = geom[0]
                        _live_positions[truck_id] = {
                            'lat': lat,
                            'lon': lon,
                            'idx': 0,
                            'geometry': geom,
                            'last_update': datetime.utcnow()
                        }
                if _live_positions:
                    return
    except Exception:
        # ignore and fall back to static seed
        pass

    # Fallback static seed (could be read from vehicle_fleet.json)
    _live_positions = {
        'truck-01': {'lat': 43.6532, 'lon': -79.3832, 'last_update': datetime.utcnow()},
        'truck-02': {'lat': 43.6426, 'lon': -79.3871, 'last_update': datetime.utcnow()},
        'truck-03': {'lat': 43.6629, 'lon': -79.3957, 'last_update': datetime.utcnow()},
    }


def _fetch_orders_from_db(limit: int = 200):
    """Fetch recent orders and items from DB and convert to OrderStop list"""
    stops = []
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        # Fetch recent orders with location info joined from mcdonalds locations if available
        cur.execute("SELECT id, franchisee_id FROM orders ORDER BY created_ts DESC LIMIT %s", (limit,))
        orders = cur.fetchall()
        for oid, franchisee in orders:
            # Try to find location coordinates for franchisee in mcdonalds_gta_locations.json via inventory tables fallback
            # As a simple approach, read location from vehicle_fleet or use static mapping: center of GTA
            # For now, assign random-ish locations in downtown Toronto for demo
            lat = 43.65 + (hash(oid) % 100) * 0.0003
            lon = -79.38 + (hash(franchisee) % 100) * -0.00025 if franchisee else -79.38

            # Sum volumes from order_items
            cur.execute("SELECT SUM(volume_cuft) FROM order_items WHERE order_id = %s", (oid,))
            vol_row = cur.fetchone()
            vol = float(vol_row[0]) if vol_row and vol_row[0] is not None else 5.0

            # Service minutes default
            service_min = 12.0

            stops.append(OrderStop(
                order_id=oid,
                franchisee_id=franchisee or "FRAN_UNKNOWN",
                location=Location(lat=lat, lon=lon),
                items_volume_cuft=vol,
                service_min=service_min
            ))

        cur.close()
        conn.close()
    except Exception as e:
        logger.exception("Failed to fetch orders from DB: %s", e)

    return stops


def _fetch_trucks_from_db():
    """Fetch vehicle fleet and convert to TruckSpec list"""
    trucks = []
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT truck_id, capacity_m3 FROM vehicle_fleet LIMIT 50")
        for truck_id, cap_m3 in cur.fetchall():
            # Convert m3 to cuft approx (1 m3 = 35.3147 cuft)
            cap_cuft = float(cap_m3) * 35.3147 if cap_m3 is not None else 100.0
            # Assign depot to one of known depots randomly
            depot_id = random.choice(list(simulator.gta_depots.keys()))
            trucks.append(TruckSpec(id=truck_id, depot_id=depot_id, capacity_cuft=cap_cuft))
        cur.close()
        conn.close()
    except Exception as e:
        logger.exception("Failed to fetch trucks from DB: %s", e)

    return trucks

def _advance_positions(seconds: int = 30):
    """Move trucks slightly along a simple vector to simulate in-transit movement."""
    for truck_id, pos in _live_positions.items():
        geom = pos.get('geometry')
        if geom and isinstance(geom, list) and len(geom) > 1:
            idx = int(pos.get('idx', 0))
            # advance index up to the end
            next_idx = min(idx + 1, len(geom) - 1)
            lon, lat = geom[next_idx]
            pos['lat'] = lat
            pos['lon'] = lon
            pos['idx'] = next_idx
            pos['last_update'] = datetime.utcnow()
        else:
            # Small random-walk step (deterministic-ish for demos)
            pos['lat'] += (hash(truck_id) % 5 - 2) * 0.00005
            pos['lon'] += ((hash(truck_id) // 3) % 5 - 2) * 0.00005
            pos['last_update'] = datetime.utcnow()


@router.post("/plan/run", response_model=PlanRunResponse)
async def plan_routes(request: PlanRunRequest) -> PlanRunResponse:
    """
    Execute route planning for a given date with trucks, depots, and stops.
    
    Features:
    - Assigns stops to nearest depots
    - Optimizes routes using nearest neighbor algorithm
    - Populates RouteStop.h3 using H3 resolution from RoutingParams.overlap_h3_res (default 8)
    - Calculates utilization_pct as volume-based: sum(load_cuft)/capacity_cuft
    - Generates loading_order in reverse delivery sequence (LIFO)
    - Detects spatial-temporal overlaps between trucks
    """
    try:
        logger.info(f"Planning routes for {request.for_date} with {len(request.trucks)} trucks and {len(request.stops)} stops")
        
        # Validate request
        if not request.trucks:
            raise HTTPException(status_code=400, detail="At least one truck is required")
        if not request.stops:
            raise HTTPException(status_code=400, detail="At least one stop is required")
        if not request.depots:
            raise HTTPException(status_code=400, detail="At least one depot is required")
        
        # Validate truck-depot relationships
        depot_ids = {depot.id for depot in request.depots}
        for truck in request.trucks:
            if truck.depot_id not in depot_ids:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Truck {truck.id} references non-existent depot {truck.depot_id}"
                )
        
        # Execute route planning
        response = simulator.plan_routes(request)
        
        logger.info(f"Generated plan {response.plan_id} with {len(response.routes)} routes in {response.runtime_s:.2f}s")
        logger.info(f"KPIs: on_time={response.kpi.on_time_pct:.1%}, overlap={response.kpi.overlap_pct:.1%}, miles_per_order={response.kpi.miles_per_order:.1f}")
        
        return response
        
    except ValueError as e:
        logger.error(f"Validation error in route planning: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error in route planning: {e}")
        raise HTTPException(status_code=500, detail="Internal server error during route planning")


@router.post('/plan/run-from-db', response_model=PlanRunResponse)
def plan_routes_from_db(for_date: Optional[str] = None, max_stops: int = 100):
    """Helper endpoint: build a PlanRunRequest from persisted orders and fleet and run planner"""
    try:
        # Build depots from simulator known depots
        depots = [Depot(id=k, location=v) for k, v in simulator.gta_depots.items()]

        trucks = _fetch_trucks_from_db()

        stops = _fetch_orders_from_db(limit=max_stops)

        if not for_date:
            for_date = datetime.utcnow().strftime('%Y-%m-%d')

        req = PlanRunRequest(
            for_date=for_date,
            depots=depots,
            trucks=trucks if trucks else [TruckSpec(id='demo-01', depot_id=depots[0].id, capacity_cuft=200.0)],
            stops=stops if stops else [],
            params=RoutingParams(),
            traffic_profile_id=None
        )

        if not req.stops:
            raise HTTPException(status_code=400, detail="No stops available from DB to plan routes")

        response = simulator.plan_routes(req)

        # Cache is populated inside simulator; return the response
        return response
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Failed to plan from DB: %s", e)
        raise HTTPException(status_code=500, detail="Failed to plan from DB")


@router.post("/reroute", response_model=ReRouteResponse)
async def reroute_plan(request: ReRouteRequest) -> ReRouteResponse:
    """
    Re-route an existing plan with limited changes.
    
    Features:
    - Supports global or truck-specific re-routing
    - Respects change_limit (0-0.6) to control modification extent
    - Computes changed_stops_pct as moved_or_resequenced / total_stops
    - Locks first N hops based on lock_hops parameter
    - Tracks reason for re-routing (incident, eta_risk, stock, manual, other)
    """
    try:
        logger.info(f"Re-routing plan {request.plan_id} with scope={request.scope}, change_limit={request.change_limit}")
        
        # Validate scope-specific requirements
        if request.scope == "truck" and not request.truck_id:
            raise HTTPException(status_code=400, detail="truck_id is required when scope=truck")
        
        # Execute re-routing
        response = simulator.reroute(request)
        
        logger.info(f"Re-routed plan {response.plan_id}: {response.changed_stops_pct:.1%} stops changed in {response.runtime_s:.2f}s")
        logger.info(f"Updated KPIs: on_time={response.kpi.on_time_pct:.1%}, overlap={response.kpi.overlap_pct:.1%}")
        
        return response
        
    except ValueError as e:
        logger.error(f"Validation error in re-routing: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error in re-routing: {e}")
        raise HTTPException(status_code=500, detail="Internal server error during re-routing")


@router.get("/kpis")
async def get_routing_kpis():
    """Get key performance indicators for routing operations"""
    try:
        # Generate mock KPIs based on current data
        # In a real system, these would come from analytics/metrics database
        kpis = {
            "on_time_pct": 94.2,
            "overlap_pct": 12.8,
            "utilization_pct": 78.5,
            "avg_stops_per_route": 8.3,
            "total_active_routes": 15,
            "completed_routes_today": 42,
            "fuel_efficiency": 85.7,
            "customer_satisfaction": 96.1
        }
        return kpis
    except Exception as e:
        logger.error(f"Error getting KPIs: {e}")
        raise HTTPException(status_code=500, detail="Internal server error getting KPIs")


@router.get("/active-routes")
async def get_active_routes():
    """Get currently active routes with real-time status"""
    try:
        # Generate mock active routes data
        # In a real system, this would query the database for current routes
        routes = [
            {
                "id": "route-001",
                "vehicle_id": "truck-01",
                "status": "ACTIVE",
                "driver": "John Smith",
                "eta": "14:30",
                "utilization": 85.0,
                "stops_remaining": 3,
                "stops_completed": 5,
                "current_location": {"lat": 43.6532, "lon": -79.3832},
                "stops": [
                    {"lat": 43.6532, "lon": -79.3832, "name": "McDonald's Queen St", "status": "completed"},
                    {"lat": 43.6626, "lon": -79.3957, "name": "McDonald's Spadina", "status": "active"},
                    {"lat": 43.6481, "lon": -79.4042, "name": "McDonald's King St", "status": "pending"}
                ]
            },
            {
                "id": "route-002",
                "vehicle_id": "truck-02",
                "status": "PLANNED",
                "driver": "Sarah Wilson",
                "eta": "15:45",
                "utilization": 72.0,
                "stops_remaining": 6,
                "stops_completed": 0,
                "current_location": {"lat": 43.6426, "lon": -79.3871},
                "stops": [
                    {"lat": 43.6426, "lon": -79.3871, "name": "McDonald's Bay St", "status": "pending"},
                    {"lat": 43.6555, "lon": -79.3986, "name": "McDonald's College St", "status": "pending"}
                ]
            },
            {
                "id": "route-003",
                "vehicle_id": "truck-03",
                "status": "DELAYED",
                "driver": "Mike Johnson",
                "eta": "16:15",
                "utilization": 91.0,
                "stops_remaining": 2,
                "stops_completed": 7,
                "current_location": {"lat": 43.6629, "lon": -79.3957},
                "stops": [
                    {"lat": 43.6629, "lon": -79.3957, "name": "McDonald's Bloor St", "status": "active"},
                    {"lat": 43.6703, "lon": -79.4163, "name": "McDonald's Ossington", "status": "pending"}
                ]
            }
        ]
        return routes
    except Exception as e:
        logger.error(f"Error getting active routes: {e}")
        raise HTTPException(status_code=500, detail="Internal server error getting active routes")


@router.get("/traffic-incidents")
async def get_traffic_incidents():
    """Get current traffic incidents affecting routes"""
    try:
        # Generate mock traffic incidents
        # In a real system, this would integrate with traffic APIs
        incidents = [
            {
                "id": "inc-001",
                "location": {"lat": 43.6532, "lon": -79.3832},
                "severity": "medium",
                "description": "Construction on Queen St",
                "delay_minutes": 15,
                "type": "construction"
            },
            {
                "id": "inc-002", 
                "location": {"lat": 43.6626, "lon": -79.3957},
                "severity": "high",
                "description": "Accident on Spadina Ave",
                "delay_minutes": 25,
                "type": "accident"
            }
        ]
        return incidents
    except Exception as e:
        logger.error(f"Error getting traffic incidents: {e}")
        raise HTTPException(status_code=500, detail="Internal server error getting traffic incidents")


@router.get("/exceptions")
async def get_exceptions():
    """Get active operational exceptions and alerts"""
    try:
        # Generate mock exceptions/alerts
        # In a real system, this would query alerts/monitoring database
        exceptions = [
            {
                "id": "exc-001",
                "type": "eta_risk",
                "severity": "high",
                "message": "Route truck-01 at risk of missing ETA by 15 minutes",
                "timestamp": "2025-10-03T14:30:00Z",
                "route_id": "route-001",
                "location": {"lat": 43.6532, "lon": -79.3832}
            },
            {
                "id": "exc-002",
                "type": "stock",
                "severity": "medium", 
                "message": "Low stock alert: Big Mac below threshold (12 remaining at Queen St)",
                "timestamp": "2025-10-03T14:25:00Z",
                "location": {"lat": 43.6532, "lon": -79.3832}
            },
            {
                "id": "exc-003",
                "type": "overlap",
                "severity": "low",
                "message": "Route overlap detected between truck-01 and truck-03",
                "timestamp": "2025-10-03T14:20:00Z"
            }
        ]

        return exceptions
    except Exception as e:
        logger.error(f"Error getting exceptions: {e}")
        raise HTTPException(status_code=500, detail="Internal server error getting exceptions")

@router.post('/route-geometry')
def get_route_geometry(body: Dict[str, Any]):
    """Return road-following route geometry (polyline) between an ordered list of coordinates.

    Request body: { "coords": [[lon, lat],[lon,lat], ...], "profile": "driving" }
    Response: { "geometry": <geojson LineString coords> }
    """
    try:
        coords = body.get('coords')
        if not coords or len(coords) < 2:
            raise ValueError('coords must be an array of at least 2 [lon,lat] pairs')

        profile = body.get('profile', 'driving')

        # Call local OSRM if available, else return straight LineString as fallback
        osrm_url = f'http://127.0.0.1:5000/route/v1/{profile}/'
        # OSRM expects lon,lat; join with ;
        coord_str = ';'.join([f"{c[0]},{c[1]}" for c in coords])
        try:
            r = requests.get(osrm_url + coord_str, params={'overview': 'full', 'geometries': 'geojson'}, timeout=2.0)
            if r.status_code == 200:
                data = r.json()
                if data.get('routes'):
                    geom = data['routes'][0]['geometry']
                    return {'geometry': geom}
        except Exception:
            # fall back silently
            pass

        # Fallback: straight line geometry
        return {'geometry': {'type': 'LineString', 'coordinates': coords}}

    except Exception as e:
        logger.error(f"Error computing route geometry: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get('/live-positions')
def get_live_positions(advance: bool = True):
    """Return simulated live GPS positions for vehicles. Query param `advance` controls stepping positions."""
    try:
        _init_live_positions_if_needed()
        if advance:
            _advance_positions()

        # Build response
        resp = []
        for truck_id, pos in _live_positions.items():
            resp.append({
                'vehicle_id': truck_id,
                'lat': pos['lat'],
                'lon': pos['lon'],
                'last_update': pos['last_update'].isoformat() + 'Z'
            })

        return resp
    except Exception as e:
        logger.error(f"Error getting live positions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def health_check():
    """Health check endpoint for routing service"""
    return {
        "status": "healthy",
        "service": "routing",
        "h3_available": hasattr(simulator, 'H3_AVAILABLE') and getattr(simulator.__class__, 'H3_AVAILABLE', False)
    }