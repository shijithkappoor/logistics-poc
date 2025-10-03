"""
Pydantic models for Orders API based on schemas/orders.api.schema.json
"""

from datetime import datetime
from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class OrderStatus(str, Enum):
    """Order status enumeration"""
    PENDING = "PENDING"
    PLANNED = "PLANNED"
    LOCKED = "LOCKED"
    ROUTED = "ROUTED"
    DELIVERED = "DELIVERED"
    QUEUED_NEXT_DAY = "QUEUED_NEXT_DAY"
    EXCEPTION = "EXCEPTION"


class LateOrderIntakeStatus(str, Enum):
    """Late order intake status enumeration"""
    QUEUED_NEXT_DAY = "QUEUED_NEXT_DAY"
    EXCEPTION = "EXCEPTION"


class OrderItem(BaseModel):
    """Order item model"""
    item_id: str
    qty: float = Field(ge=0, description="Quantity, must be non-negative")
    volume_cuft: float = Field(ge=0, description="Volume in cubic feet, must be non-negative")
    non_substitutable: bool = Field(description="Whether item can be substituted")

    class Config:
        extra = "forbid"


class Order(BaseModel):
    """Order model"""
    id: str
    franchisee_id: str
    created_ts: datetime = Field(description="ISO datetime when order was created")
    window_start: str = Field(pattern=r"^\d{2}:\d{2}$", description="HH:MM local (e.g., 04:00)")
    window_end: str = Field(pattern=r"^\d{2}:\d{2}$", description="HH:MM local (e.g., 10:00)")
    status: OrderStatus
    notes: Optional[str] = None
    items: List[OrderItem] = Field(min_items=1, description="List of order items")

    class Config:
        extra = "forbid"


class DistributionSettings(BaseModel):
    """Optional distribution settings for order generation"""
    cluster_strength: float = Field(default=0.6, ge=0, le=1, description="Clustering strength")
    item_mix_bias: Optional[Dict[str, float]] = Field(default=None, description="Item mix bias")
    qty_scale: float = Field(default=1.0, ge=0.1, le=10, description="Quantity scale factor")

    class Config:
        extra = "forbid"


class GenerateOrdersRequest(BaseModel):
    """Request model for generating orders"""
    count: int = Field(ge=1, le=5000, description="Number of orders to generate")
    date: Optional[str] = Field(default=None, pattern=r"^\d{4}-\d{2}-\d{2}$", description="Service date (YYYY-MM-DD)")
    window_start: str = Field(default="04:00", pattern=r"^\d{2}:\d{2}$", description="Default window start time")
    window_end: str = Field(default="10:00", pattern=r"^\d{2}:\d{2}$", description="Default window end time")
    distributions: Optional[DistributionSettings] = Field(default=None, description="Distribution settings")

    class Config:
        extra = "forbid"


class GenerateOrdersResponse(BaseModel):
    """Response model for generating orders"""
    orders_created: int = Field(ge=0, description="Number of orders created")
    order_ids: List[str] = Field(description="List of created order IDs")

    class Config:
        extra = "forbid"


class ListOrdersQuery(BaseModel):
    """Query parameters for listing orders"""
    status: Optional[OrderStatus] = None
    franchisee_id: Optional[str] = None
    created_after: Optional[datetime] = None
    created_before: Optional[datetime] = None
    limit: int = Field(default=100, ge=1, le=500, description="Maximum number of orders to return")
    offset: int = Field(default=0, ge=0, description="Number of orders to skip")

    class Config:
        extra = "forbid"


class ListOrdersResponse(BaseModel):
    """Response model for listing orders"""
    total: int = Field(ge=0, description="Total number of orders matching criteria")
    orders: List[Order] = Field(description="List of orders")

    class Config:
        extra = "forbid"


class GetOrderResponse(BaseModel):
    """Response model for getting a single order (alias for Order)"""
    id: str
    franchisee_id: str
    created_ts: datetime
    window_start: str = Field(pattern=r"^\d{2}:\d{2}$")
    window_end: str = Field(pattern=r"^\d{2}:\d{2}$")
    status: OrderStatus
    notes: Optional[str] = None
    items: List[OrderItem] = Field(min_items=1)

    class Config:
        extra = "forbid"


class LateOrderIntakeRequest(BaseModel):
    """Request model for late order intake"""
    items: List[OrderItem] = Field(min_items=1, description="List of order items")
    franchisee_id: str
    received_ts: datetime = Field(description="ISO datetime when order was received")
    is_standalone_item: Optional[bool] = Field(default=None, description="Auto-queue for next day if after 23:00")

    class Config:
        extra = "forbid"


class LateOrderIntakeResponse(BaseModel):
    """Response model for late order intake"""
    status: LateOrderIntakeStatus
    order_id: str

    class Config:
        extra = "forbid"