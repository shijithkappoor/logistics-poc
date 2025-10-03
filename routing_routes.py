"""
FastAPI router for routing endpoints
"""
from fastapi import APIRouter, HTTPException, status
from routing_models import PlanRunRequest, ReRouteRequest, PlanRunResponse, ReRouteResponse
from routing_simulator import RoutingSimulator
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/routing", tags=["routing"])

# Initialize simulator
simulator = RoutingSimulator()


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


@router.get("/health")
async def health_check():
    """Health check endpoint for routing service"""
    return {
        "status": "healthy",
        "service": "routing",
        "h3_available": hasattr(simulator, 'H3_AVAILABLE') and getattr(simulator.__class__, 'H3_AVAILABLE', False)
    }