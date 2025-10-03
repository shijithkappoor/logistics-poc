"""
Pydantic models for the Inventory API based on inventory.api.schema.json
"""
from datetime import datetime
from typing import List, Optional, Union
from pydantic import BaseModel, Field
from enum import Enum


# Core record models
class LocationType(str, Enum):
    WAREHOUSE = "warehouse"
    FRANCHISEE = "franchisee"


class StockRecord(BaseModel):
    location_type: LocationType
    location_id: str
    item_id: str
    qty: float = Field(..., ge=0)


class ReservationRecord(BaseModel):
    reservation_id: str
    warehouse_id: str
    order_id: str
    item_id: str
    qty: float = Field(..., ge=0)
    ts: datetime
    expires_ts: Optional[datetime] = None


# Snapshot models
class SnapshotQuery(BaseModel):
    as_of: Optional[datetime] = None
    location_type: Optional[LocationType] = None
    location_id: Optional[str] = None
    item_ids: Optional[List[str]] = None
    include_reservations: bool = Field(default=True)


class SnapshotResponse(BaseModel):
    server_ts: datetime
    stock: List[StockRecord]
    reservations: Optional[List[ReservationRecord]] = None


# Reservation models
class ReservationLine(BaseModel):
    warehouse_id: str
    order_id: str
    item_id: str
    qty: float = Field(..., ge=0)
    non_substitutable: bool


class ReserveRequest(BaseModel):
    plan_id: str
    lines: List[ReservationLine] = Field(..., min_length=1)
    ttl_minutes: int = Field(default=480, ge=5, le=720, description="TTL defaults to 480 min (8h)")


class ReservationStatus(str, Enum):
    OK = "ok"
    PARTIAL = "partial"
    FAILED = "failed"


class InsufficientStock(BaseModel):
    warehouse_id: str
    item_id: str
    requested: float = Field(..., ge=0)
    available: float = Field(..., ge=0)


class ReserveResponse(BaseModel):
    status: ReservationStatus
    reservations: List[ReservationRecord]
    insufficient: List[InsufficientStock]


class ReleaseRequest(BaseModel):
    plan_id: Optional[str] = None
    reservation_ids: Optional[List[str]] = None


class ReleaseResponse(BaseModel):
    released: List[str]
    not_found: List[str]


# Stock event models
class StockEventType(str, Enum):
    REPLENISH = "replenish"
    TRANSFER = "transfer"
    CONSUME = "consume"
    CORRECTION = "correction"


class StockEvent(BaseModel):
    id: str
    type: StockEventType
    ts: datetime
    warehouse_id: Optional[str] = None
    from_warehouse_id: Optional[str] = None
    to_warehouse_id: Optional[str] = None
    franchisee_id: Optional[str] = None
    item_id: str
    qty: float = Field(..., ge=0)
    reason: Optional[str] = None

    def model_validate(self, value):
        if isinstance(value, dict):
            event_type = value.get('type')
            
            # Validate required fields based on event type
            if event_type == 'transfer':
                if not value.get('from_warehouse_id') or not value.get('to_warehouse_id'):
                    raise ValueError('transfer events require from_warehouse_id and to_warehouse_id')
            elif event_type == 'replenish':
                if not value.get('warehouse_id'):
                    raise ValueError('replenish events require warehouse_id')
            elif event_type == 'consume':
                if not value.get('franchisee_id'):
                    raise ValueError('consume events require franchisee_id')
        
        return super().model_validate(value)


# Use List[StockEvent] directly for PostEventsRequest
PostEventsRequest = List[StockEvent]


class RejectedEvent(BaseModel):
    id: str
    error: str


class PostEventsResponse(BaseModel):
    accepted: int = Field(..., ge=0)
    rejected: List[RejectedEvent]


# Feasibility models
class FeasibilityLine(BaseModel):
    order_id: str
    warehouse_id: str
    item_id: str
    qty: float = Field(..., ge=0)
    non_substitutable: bool


class FeasibilityRequest(BaseModel):
    lines: List[FeasibilityLine] = Field(..., min_length=1)


class InsufficientFeasibility(BaseModel):
    order_id: str
    warehouse_id: str
    item_id: str
    required: float = Field(..., ge=0)
    available: float = Field(..., ge=0)
    non_substitutable_blocked: bool = Field(default=False, description="Bubble alert to orchestrator if True")


class FeasibilityResponse(BaseModel):
    ok: bool
    insufficient: List[InsufficientFeasibility]