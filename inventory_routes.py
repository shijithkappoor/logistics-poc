"""
FastAPI router for inventory endpoints
"""
from fastapi import APIRouter, HTTPException, Query, status
from typing import Optional, List
from datetime import datetime
import logging

from inventory_models import (
    SnapshotQuery, SnapshotResponse, ReserveRequest, ReserveResponse,
    ReleaseRequest, ReleaseResponse, PostEventsRequest, PostEventsResponse,
    FeasibilityRequest, FeasibilityResponse, LocationType
)
from inventory_simulator import InventorySimulator

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/inventory", tags=["inventory"])

# Initialize simulator
simulator = InventorySimulator()


@router.get("/snapshot", response_model=SnapshotResponse)
async def get_inventory_snapshot(
    as_of: Optional[datetime] = Query(None, description="Snapshot timestamp (defaults to current time)"),
    location_type: Optional[LocationType] = Query(None, description="Filter by location type"),
    location_id: Optional[str] = Query(None, description="Filter by specific location ID"),
    item_ids: Optional[List[str]] = Query(None, description="Filter by specific item IDs"),
    include_reservations: bool = Query(True, description="Include active reservations in response")
) -> SnapshotResponse:
    """
    Get inventory snapshot with optional filtering.
    
    Features:
    - Real-time stock levels across warehouses and franchisees
    - Active reservations with TTL tracking
    - Flexible filtering by location type, location ID, and item IDs
    - Historical snapshots with as_of timestamp
    """
    try:
        query = SnapshotQuery(
            as_of=as_of,
            location_type=location_type,
            location_id=location_id,
            item_ids=item_ids,
            include_reservations=include_reservations
        )
        
        response = simulator.get_snapshot(query)
        
        logger.info(f"Snapshot generated: {len(response.stock)} stock records, "
                   f"{len(response.reservations or [])} reservations")
        
        return response
        
    except Exception as e:
        logger.error(f"Error generating snapshot: {e}")
        raise HTTPException(status_code=500, detail="Internal server error during snapshot generation")


@router.post("/reserve", response_model=ReserveResponse)
async def reserve_inventory(request: ReserveRequest) -> ReserveResponse:
    """
    Reserve inventory at plan lock time with TTL (defaults to 480 min / 8h).
    
    Features:
    - Plan-based reservation tracking
    - Configurable TTL (5-720 minutes, default 480)
    - Non-substitutable item handling with orchestrator alerts
    - Partial reservation support with detailed insufficient stock reporting
    """
    try:
        logger.info(f"Processing reservation for plan {request.plan_id} with {len(request.lines)} items, TTL={request.ttl_minutes}min")
        
        # Validate request
        if not request.lines:
            raise HTTPException(status_code=400, detail="At least one reservation line is required")
        
        response = simulator.reserve_stock(request)
        
        # Check for non-substitutable blocking alerts
        non_substitutable_issues = [
            line for line in request.lines 
            if line.non_substitutable and any(
                ins.item_id == line.item_id and ins.warehouse_id == line.warehouse_id 
                for ins in response.insufficient
            )
        ]
        
        if non_substitutable_issues:
            logger.error(f"ORCHESTRATOR ALERT: Non-substitutable items blocked for plan {request.plan_id}")
            logger.error(f"Affected items: {[f'{line.item_id}@{line.warehouse_id}' for line in non_substitutable_issues]}")
            logger.error("Recommendation: Queue for next day or trigger exception handling")
        
        logger.info(f"Reservation completed: {response.status}, {len(response.reservations)} reserved, {len(response.insufficient)} insufficient")
        
        return response
        
    except ValueError as e:
        logger.error(f"Validation error in reservation: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error in reservation processing: {e}")
        raise HTTPException(status_code=500, detail="Internal server error during reservation")


@router.post("/release", response_model=ReleaseResponse)
async def release_reservations(request: ReleaseRequest) -> ReleaseResponse:
    """
    Release inventory reservations by plan ID or specific reservation IDs.
    
    Features:
    - Bulk release by plan ID
    - Selective release by reservation IDs
    - Detailed tracking of released vs not found reservations
    """
    try:
        if not request.plan_id and not request.reservation_ids:
            raise HTTPException(status_code=400, detail="Either plan_id or reservation_ids must be provided")
        
        logger.info(f"Releasing reservations: plan_id={request.plan_id}, "
                   f"reservation_ids={len(request.reservation_ids or [])}")
        
        response = simulator.release_stock(request)
        
        logger.info(f"Release completed: {len(response.released)} released, {len(response.not_found)} not found")
        
        return response
        
    except Exception as e:
        logger.error(f"Error in release processing: {e}")
        raise HTTPException(status_code=500, detail="Internal server error during release")


@router.post("/events", response_model=PostEventsResponse)
async def post_stock_events(events: PostEventsRequest) -> PostEventsResponse:
    """
    Process mid-run stock events that update inventory and may trigger re-route suggestions.
    
    Features:
    - Multiple event types: replenish, transfer, consume, correction
    - Atomic event processing with detailed error reporting
    - Real-time inventory updates affecting feasibility
    - Integration with routing system for stock-based re-route triggers
    """
    try:
        if not events:
            raise HTTPException(status_code=400, detail="At least one event is required")
        
        logger.info(f"Processing {len(events)} stock events")
        
        response = simulator.process_events(events)
        
        logger.info(f"Events processed: {response.accepted} accepted, {len(response.rejected)} rejected")
        
        # Log potential re-route triggers
        if response.accepted > 0:
            logger.info("Stock events processed - feasibility may have changed, consider re-route check (reason=stock)")
        
        return response
        
    except Exception as e:
        logger.error(f"Error processing stock events: {e}")
        raise HTTPException(status_code=500, detail="Internal server error during event processing")


@router.post("/feasibility", response_model=FeasibilityResponse)
async def check_feasibility(request: FeasibilityRequest) -> FeasibilityResponse:
    """
    Check feasibility of fulfilling orders with current stock levels.
    
    Features:
    - Real-time feasibility checking against current stock and reservations
    - Non-substitutable item blocking with orchestrator alerts
    - Detailed insufficient stock reporting per order
    - Integration point for triggering re-route suggestions (reason=stock)
    """
    try:
        if not request.lines:
            raise HTTPException(status_code=400, detail="At least one feasibility line is required")
        
        logger.info(f"Checking feasibility for {len(request.lines)} order lines")
        
        response = simulator.check_feasibility(request)
        
        # Check for non-substitutable blocking
        non_sub_blocked = any(ins.non_substitutable_blocked for ins in response.insufficient)
        
        if non_sub_blocked:
            logger.error("ORCHESTRATOR ALERT: Non-substitutable items insufficient!")
            logger.error("Recommendation: Queue affected orders for next day or trigger exception handling")
        
        if not response.ok and not non_sub_blocked:
            logger.warning("Feasibility check failed - consider triggering re-route (reason=stock)")
        
        logger.info(f"Feasibility check completed: {'OK' if response.ok else 'BLOCKED'}, "
                   f"{len(response.insufficient)} insufficient items")
        
        return response
        
    except Exception as e:
        logger.error(f"Error in feasibility check: {e}")
        raise HTTPException(status_code=500, detail="Internal server error during feasibility check")


@router.get("/health")
async def health_check():
    """Health check endpoint for inventory service"""
    try:
        metrics = simulator.get_metrics()
        return {
            "status": "healthy",
            "service": "inventory",
            "metrics": metrics
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail="Service unhealthy")


@router.get("/metrics")
async def get_metrics():
    """Get detailed inventory metrics for monitoring"""
    try:
        metrics = simulator.get_metrics()
        return metrics
    except Exception as e:
        logger.error(f"Error retrieving metrics: {e}")
        raise HTTPException(status_code=500, detail="Error retrieving metrics")