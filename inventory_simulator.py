"""
Inventory simulator for stock tracking, reservation management, and event processing
"""
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, field
from threading import Lock
import logging

from inventory_models import (
    StockRecord, ReservationRecord, LocationType, StockEvent, StockEventType,
    SnapshotQuery, SnapshotResponse, ReserveRequest, ReserveResponse, ReservationStatus,
    ReleaseRequest, ReleaseResponse, PostEventsRequest, PostEventsResponse,
    FeasibilityRequest, FeasibilityResponse, InsufficientStock, InsufficientFeasibility,
    RejectedEvent, ReservationLine, FeasibilityLine
)

logger = logging.getLogger(__name__)


@dataclass
class InventoryState:
    """Thread-safe inventory state management"""
    stock: Dict[Tuple[str, str, str], float] = field(default_factory=dict)  # (location_type, location_id, item_id) -> qty
    reservations: Dict[str, ReservationRecord] = field(default_factory=dict)  # reservation_id -> record
    plan_reservations: Dict[str, Set[str]] = field(default_factory=dict)  # plan_id -> set of reservation_ids
    events: List[StockEvent] = field(default_factory=list)
    lock: Lock = field(default_factory=Lock)


class InventorySimulator:
    """
    Inventory management simulator with reservation TTL, non-substitutable handling, and event processing
    """
    
    def __init__(self):
        self.state = InventoryState()
        
        # Initialize sample stock data for GTA warehouses
        self._initialize_sample_stock()
    
    def _initialize_sample_stock(self):
        """Initialize sample inventory for testing"""
        sample_items = [
            "BREAD_WHITE", "BREAD_WHOLE", "MILK_2PCT", "MILK_SKIM", "EGGS_DOZEN",
            "BUTTER_SALTED", "CHEESE_CHEDDAR", "YOGURT_VANILLA", "APPLES_GALA", "BANANAS",
            "CHICKEN_BREAST", "GROUND_BEEF", "SALMON_FILLET", "PASTA_PENNE", "RICE_BASMATI",
            "TOMATO_SAUCE", "OLIVE_OIL", "ONIONS_YELLOW", "POTATOES_RUSSET", "CARROTS"
        ]
        
        warehouses = ["WH_NORTH", "WH_WEST", "WH_EAST", "WH_CENTRAL"]
        franchisees = ["FRAN_001", "FRAN_002", "FRAN_003", "FRAN_004", "FRAN_005"]
        
        with self.state.lock:
            # Warehouse stock
            for warehouse in warehouses:
                for item in sample_items:
                    # Vary stock levels realistically
                    base_qty = 100
                    if "BREAD" in item or "MILK" in item:
                        base_qty = 200  # High turnover items
                    elif "MEAT" in item or "CHICKEN" in item or "SALMON" in item:
                        base_qty = 50   # Lower stock for perishables
                    
                    qty = base_qty + hash(f"{warehouse}_{item}") % 100
                    key = (LocationType.WAREHOUSE, warehouse, item)
                    self.state.stock[key] = float(qty)
            
            # Franchisee stock (lower quantities)
            for franchisee in franchisees:
                for item in sample_items[:10]:  # Franchisees carry fewer items
                    qty = 10 + hash(f"{franchisee}_{item}") % 20
                    key = (LocationType.FRANCHISEE, franchisee, item)
                    self.state.stock[key] = float(qty)
    
    def _get_stock_key(self, location_type: str, location_id: str, item_id: str) -> Tuple[str, str, str]:
        """Generate stock key tuple"""
        return (location_type, location_id, item_id)
    
    def _clean_expired_reservations(self):
        """Remove expired reservations"""
        now = datetime.now()
        expired_ids = []
        
        for res_id, reservation in self.state.reservations.items():
            if reservation.expires_ts and reservation.expires_ts <= now:
                expired_ids.append(res_id)
        
        for res_id in expired_ids:
            reservation = self.state.reservations.pop(res_id)
            # Remove from plan mapping
            for plan_id, res_set in self.state.plan_reservations.items():
                res_set.discard(res_id)
            logger.info(f"Expired reservation {res_id} for {reservation.qty} units of {reservation.item_id}")
    
    def get_snapshot(self, query: SnapshotQuery) -> SnapshotResponse:
        """Get inventory snapshot with optional filtering"""
        with self.state.lock:
            self._clean_expired_reservations()
            
            # Filter stock records
            stock_records = []
            for (loc_type, loc_id, item_id), qty in self.state.stock.items():
                # Apply filters
                if query.location_type and loc_type != query.location_type:
                    continue
                if query.location_id and loc_id != query.location_id:
                    continue
                if query.item_ids and item_id not in query.item_ids:
                    continue
                
                stock_records.append(StockRecord(
                    location_type=LocationType(loc_type),
                    location_id=loc_id,
                    item_id=item_id,
                    qty=qty
                ))
            
            # Include reservations if requested
            reservations = None
            if query.include_reservations:
                reservations = list(self.state.reservations.values())
            
            return SnapshotResponse(
                server_ts=query.as_of or datetime.now(),
                stock=stock_records,
                reservations=reservations
            )
    
    def reserve_stock(self, request: ReserveRequest) -> ReserveResponse:
        """Reserve stock with TTL and non-substitutable handling"""
        with self.state.lock:
            self._clean_expired_reservations()
            
            reservations = []
            insufficient = []
            now = datetime.now()
            expires_ts = now + timedelta(minutes=request.ttl_minutes)
            
            # Track what we can/cannot reserve
            can_reserve_all = True
            non_substitutable_blocked = False
            
            for line in request.lines:
                stock_key = self._get_stock_key(LocationType.WAREHOUSE, line.warehouse_id, line.item_id)
                available_qty = self.state.stock.get(stock_key, 0.0)
                
                # Calculate already reserved quantity
                reserved_qty = sum(
                    res.qty for res in self.state.reservations.values()
                    if res.warehouse_id == line.warehouse_id and res.item_id == line.item_id
                )
                
                net_available = available_qty - reserved_qty
                
                if line.qty <= net_available:
                    # Can reserve this item
                    reservation_id = str(uuid.uuid4())
                    reservation = ReservationRecord(
                        reservation_id=reservation_id,
                        warehouse_id=line.warehouse_id,
                        order_id=line.order_id,
                        item_id=line.item_id,
                        qty=line.qty,
                        ts=now,
                        expires_ts=expires_ts
                    )
                    
                    reservations.append(reservation)
                    self.state.reservations[reservation_id] = reservation
                    
                    # Track by plan
                    if request.plan_id not in self.state.plan_reservations:
                        self.state.plan_reservations[request.plan_id] = set()
                    self.state.plan_reservations[request.plan_id].add(reservation_id)
                    
                else:
                    # Insufficient stock
                    can_reserve_all = False
                    insufficient.append(InsufficientStock(
                        warehouse_id=line.warehouse_id,
                        item_id=line.item_id,
                        requested=line.qty,
                        available=net_available
                    ))
                    
                    # Check if this blocks non-substitutable items
                    if line.non_substitutable:
                        non_substitutable_blocked = True
                        logger.warning(f"Non-substitutable item {line.item_id} insufficient: requested {line.qty}, available {net_available}")
            
            # Determine status
            if can_reserve_all:
                status = ReservationStatus.OK
            elif reservations:  # Some reservations made
                status = ReservationStatus.PARTIAL
            else:  # No reservations made
                status = ReservationStatus.FAILED
            
            logger.info(f"Reservation for plan {request.plan_id}: {status}, {len(reservations)} items reserved, {len(insufficient)} insufficient")
            
            if non_substitutable_blocked:
                logger.error(f"ALERT: Non-substitutable items blocked for plan {request.plan_id} - consider queuing for next day or triggering exception")
            
            return ReserveResponse(
                status=status,
                reservations=reservations,
                insufficient=insufficient
            )
    
    def release_stock(self, request: ReleaseRequest) -> ReleaseResponse:
        """Release reservations by plan or specific reservation IDs"""
        with self.state.lock:
            released = []
            not_found = []
            
            if request.plan_id:
                # Release all reservations for a plan
                plan_reservations = self.state.plan_reservations.get(request.plan_id, set())
                for res_id in list(plan_reservations):
                    if res_id in self.state.reservations:
                        del self.state.reservations[res_id]
                        plan_reservations.discard(res_id)
                        released.append(res_id)
                    else:
                        not_found.append(res_id)
                
                # Clean up empty plan entry
                if not plan_reservations:
                    self.state.plan_reservations.pop(request.plan_id, None)
            
            if request.reservation_ids:
                # Release specific reservations
                for res_id in request.reservation_ids:
                    if res_id in self.state.reservations:
                        reservation = self.state.reservations.pop(res_id)
                        # Remove from plan mapping
                        for plan_id, res_set in self.state.plan_reservations.items():
                            res_set.discard(res_id)
                        released.append(res_id)
                    else:
                        not_found.append(res_id)
            
            logger.info(f"Released {len(released)} reservations, {len(not_found)} not found")
            
            return ReleaseResponse(
                released=released,
                not_found=not_found
            )
    
    def process_events(self, events: PostEventsRequest) -> PostEventsResponse:
        """Process stock events and update inventory"""
        with self.state.lock:
            accepted = 0
            rejected = []
            
            for event in events:
                try:
                    self._validate_event(event)
                    self._apply_event(event)
                    self.state.events.append(event)
                    accepted += 1
                    logger.info(f"Applied event {event.id}: {event.type} {event.qty} of {event.item_id}")
                    
                except Exception as e:
                    rejected.append(RejectedEvent(
                        id=event.id,
                        error=str(e)
                    ))
                    logger.error(f"Rejected event {event.id}: {e}")
            
            return PostEventsResponse(
                accepted=accepted,
                rejected=rejected
            )
    
    def _validate_event(self, event: StockEvent):
        """Validate event requirements"""
        if event.type == StockEventType.TRANSFER:
            if not event.from_warehouse_id or not event.to_warehouse_id:
                raise ValueError("Transfer events require from_warehouse_id and to_warehouse_id")
        elif event.type == StockEventType.REPLENISH:
            if not event.warehouse_id:
                raise ValueError("Replenish events require warehouse_id")
        elif event.type == StockEventType.CONSUME:
            if not event.franchisee_id:
                raise ValueError("Consume events require franchisee_id")
    
    def _apply_event(self, event: StockEvent):
        """Apply stock event to inventory"""
        if event.type == StockEventType.REPLENISH:
            # Add stock to warehouse
            key = self._get_stock_key(LocationType.WAREHOUSE, event.warehouse_id, event.item_id)
            current_qty = self.state.stock.get(key, 0.0)
            self.state.stock[key] = current_qty + event.qty
            
        elif event.type == StockEventType.CONSUME:
            # Remove stock from franchisee
            key = self._get_stock_key(LocationType.FRANCHISEE, event.franchisee_id, event.item_id)
            current_qty = self.state.stock.get(key, 0.0)
            self.state.stock[key] = max(0.0, current_qty - event.qty)
            
        elif event.type == StockEventType.TRANSFER:
            # Move stock between warehouses
            from_key = self._get_stock_key(LocationType.WAREHOUSE, event.from_warehouse_id, event.item_id)
            to_key = self._get_stock_key(LocationType.WAREHOUSE, event.to_warehouse_id, event.item_id)
            
            from_qty = self.state.stock.get(from_key, 0.0)
            to_qty = self.state.stock.get(to_key, 0.0)
            
            if from_qty < event.qty:
                raise ValueError(f"Insufficient stock for transfer: {from_qty} < {event.qty}")
            
            self.state.stock[from_key] = from_qty - event.qty
            self.state.stock[to_key] = to_qty + event.qty
            
        elif event.type == StockEventType.CORRECTION:
            # Inventory correction - set absolute quantity
            if event.warehouse_id:
                key = self._get_stock_key(LocationType.WAREHOUSE, event.warehouse_id, event.item_id)
            elif event.franchisee_id:
                key = self._get_stock_key(LocationType.FRANCHISEE, event.franchisee_id, event.item_id)
            else:
                raise ValueError("Correction events require warehouse_id or franchisee_id")
            
            self.state.stock[key] = event.qty
    
    def check_feasibility(self, request: FeasibilityRequest) -> FeasibilityResponse:
        """Check feasibility of fulfilling orders with current stock"""
        with self.state.lock:
            self._clean_expired_reservations()
            
            insufficient = []
            non_substitutable_blocked = False
            
            # Group requests by warehouse and item for efficiency
            requirements = {}  # (warehouse_id, item_id) -> [(order_id, qty, non_substitutable), ...]
            
            for line in request.lines:
                key = (line.warehouse_id, line.item_id)
                if key not in requirements:
                    requirements[key] = []
                requirements[key].append((line.order_id, line.qty, line.non_substitutable))
            
            # Check each requirement group
            for (warehouse_id, item_id), orders in requirements.items():
                stock_key = self._get_stock_key(LocationType.WAREHOUSE, warehouse_id, item_id)
                available_qty = self.state.stock.get(stock_key, 0.0)
                
                # Calculate already reserved quantity
                reserved_qty = sum(
                    res.qty for res in self.state.reservations.values()
                    if res.warehouse_id == warehouse_id and res.item_id == item_id
                )
                
                net_available = available_qty - reserved_qty
                total_required = sum(qty for _, qty, _ in orders)
                
                if total_required > net_available:
                    # Insufficient stock - identify which orders are affected
                    remaining_available = net_available
                    
                    for order_id, qty, non_substitutable in orders:
                        if qty > remaining_available:
                            insufficient.append(InsufficientFeasibility(
                                order_id=order_id,
                                warehouse_id=warehouse_id,
                                item_id=item_id,
                                required=qty,
                                available=max(0.0, remaining_available),
                                non_substitutable_blocked=non_substitutable
                            ))
                            
                            if non_substitutable:
                                non_substitutable_blocked = True
                        else:
                            remaining_available -= qty
            
            is_feasible = len(insufficient) == 0
            
            if non_substitutable_blocked:
                logger.warning("FEASIBILITY ALERT: Non-substitutable items insufficient - may require re-route (reason=stock)")
            
            logger.info(f"Feasibility check: {'OK' if is_feasible else 'BLOCKED'}, {len(insufficient)} insufficient items")
            
            return FeasibilityResponse(
                ok=is_feasible,
                insufficient=insufficient
            )
    
    def get_metrics(self) -> Dict:
        """Get inventory metrics for monitoring"""
        with self.state.lock:
            self._clean_expired_reservations()
            
            total_stock_items = len(self.state.stock)
            total_stock_qty = sum(self.state.stock.values())
            active_reservations = len(self.state.reservations)
            total_reserved_qty = sum(res.qty for res in self.state.reservations.values())
            
            return {
                "total_stock_items": total_stock_items,
                "total_stock_qty": total_stock_qty,
                "active_reservations": active_reservations,
                "total_reserved_qty": total_reserved_qty,
                "events_processed": len(self.state.events),
                "active_plans": len(self.state.plan_reservations)
            }