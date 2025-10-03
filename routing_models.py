"""
Pydantic models for the Routing API based on routing.api.schema.json
"""
from datetime import datetime
from typing import List, Optional, Literal
from pydantic import BaseModel, Field
from enum import Enum


# Core types
class Location(BaseModel):
    lat: float = Field(..., ge=-90, le=90, description="Latitude")
    lon: float = Field(..., ge=-180, le=180, description="Longitude")


# Input models
class OrderStop(BaseModel):
    order_id: str
    franchisee_id: str
    location: Location
    items_volume_cuft: float = Field(..., ge=0)
    service_min: float = Field(default=15, ge=0)
    window_start: str = Field(default="04:00", pattern=r"^\d{2}:\d{2}$")
    window_end: str = Field(default="10:00", pattern=r"^\d{2}:\d{2}$")
    non_substitutable_present: bool = Field(default=False)


class Depot(BaseModel):
    id: str
    location: Location


class TruckSpec(BaseModel):
    id: str
    depot_id: str
    capacity_cuft: float = Field(..., ge=0)


class RoutingParams(BaseModel):
    delivery_window_start: str = Field(default="04:00", pattern=r"^\d{2}:\d{2}$")
    delivery_window_end: str = Field(default="10:00", pattern=r"^\d{2}:\d{2}$")
    service_time_min: float = Field(default=15, ge=0)
    overlap_h3_res: int = Field(default=8, ge=4, le=15)
    avoid_overlap_weight: float = Field(default=1.0, ge=0)
    unused_truck_weight: float = Field(default=0.3, ge=0)
    change_cost_weight: float = Field(default=2.0, ge=0)
    max_change_ratio: float = Field(default=0.3, ge=0, le=0.6, description="For re-route; 0..0.6")


# Request models
class PlanRunRequest(BaseModel):
    for_date: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}$")
    depots: List[Depot] = Field(..., min_length=1)
    trucks: List[TruckSpec] = Field(..., min_length=1)
    stops: List[OrderStop] = Field(..., min_length=1)
    params: Optional[RoutingParams] = Field(default_factory=RoutingParams)
    traffic_profile_id: Optional[str] = Field(None, description="Use current or forecasted profile id")


class ReRouteScope(str, Enum):
    GLOBAL = "global"
    TRUCK = "truck"


class ReRouteReason(str, Enum):
    INCIDENT = "incident"
    ETA_RISK = "eta_risk"
    STOCK = "stock"
    MANUAL = "manual"
    OTHER = "other"


class ReRouteRequest(BaseModel):
    plan_id: str
    scope: ReRouteScope
    truck_id: Optional[str] = Field(None, description="required when scope=truck")
    change_limit: float = Field(..., ge=0, le=0.6)
    lock_hops: int = Field(..., ge=1, le=3)
    params: Optional[RoutingParams] = Field(default_factory=RoutingParams)
    reason: Optional[ReRouteReason] = None

    @classmethod
    def model_validate(cls, v):
        if isinstance(v, dict):
            if v.get('scope') == 'truck' and not v.get('truck_id'):
                raise ValueError('truck_id is required when scope=truck')
        return super().model_validate(v)


# Output models
class OverlapIncident(BaseModel):
    h3: str = Field(..., description="H3 cell identifier")
    start_ts: datetime
    end_ts: datetime
    truck_ids: List[str] = Field(..., min_length=2)


class StopType(str, Enum):
    DELIVERY = "delivery"
    PICKUP = "pickup"
    DEPOT = "depot"


class RouteStop(BaseModel):
    stop_id: str = Field(..., description="Order id or internal stop id")
    type: StopType
    location: Location
    eta: datetime
    eta_ci_low_min: Optional[float] = None
    eta_ci_high_min: Optional[float] = None
    service_min: float
    load_cuft: float = Field(..., ge=0)
    h3: Optional[str] = Field(None, description="H3 cell identifier populated from RoutingParams.overlap_h3_res")


class RouteSummary(BaseModel):
    truck_id: str
    stops: List[RouteStop]
    distance_km: float
    drive_time_min: float
    utilization_pct: float = Field(..., ge=0, le=1, description="Volume-based: sum(load_cuft)/capacity_cuft")


class PickTask(BaseModel):
    seq: int = Field(..., ge=1)
    aisle: str
    bin: str
    item_id: str
    qty: float = Field(..., ge=0)


class PickPackOutput(BaseModel):
    truck_id: str
    pick_sequence: List[PickTask]
    loading_order: List[str] = Field(..., description="Stop ids in reverse delivery order for last-out-first-in loading")


class PlanKPI(BaseModel):
    on_time_pct: float = Field(..., ge=0, le=1)
    overlap_pct: float = Field(..., ge=0, le=1)
    miles_per_order: float = Field(..., ge=0)
    runtime_s: Optional[float] = Field(None, ge=0)


# Response models
class PlanRunResponse(BaseModel):
    plan_id: str
    runtime_s: float = Field(..., ge=0)
    routes: List[RouteSummary]
    overlap_incidents: List[OverlapIncident]
    kpi: PlanKPI
    pickpack: List[PickPackOutput]


class ReRouteResponse(BaseModel):
    plan_id: str
    changed_stops_pct: float = Field(..., ge=0, le=1, description="moved_or_resequenced / total_stops")
    runtime_s: float = Field(..., ge=0)
    routes: List[RouteSummary]
    overlap_incidents: List[OverlapIncident]
    kpi: PlanKPI