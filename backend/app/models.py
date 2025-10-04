from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum
import uuid
import random


class OrderStatus(str, Enum):
    PENDING = "PENDING"
    PLANNED = "PLANNED"
    LOCKED = "LOCKED"
    ROUTED = "ROUTED"
    DELIVERED = "DELIVERED"
    QUEUED_NEXT_DAY = "QUEUED_NEXT_DAY"
    EXCEPTION = "EXCEPTION"


class LateIntakeStatus(str, Enum):
    QUEUED_NEXT_DAY = "QUEUED_NEXT_DAY"
    EXCEPTION = "EXCEPTION"


class OrderItem(BaseModel):
    item_id: str
    qty: float = Field(ge=0)
    volume_cuft: float = Field(ge=0)
    non_substitutable: bool

    class Config:
        extra = "forbid"


class Order(BaseModel):
    id: str
    franchisee_id: str
    created_ts: datetime
    window_start: str = Field(pattern=r"^\d{2}:\d{2}$", description="HH:MM local (e.g., 04:00)")
    window_end: str = Field(pattern=r"^\d{2}:\d{2}$", description="HH:MM local (e.g., 10:00)")
    status: OrderStatus
    notes: Optional[str] = None
    items: List[OrderItem] = Field(min_items=1)

    class Config:
        extra = "forbid"


class GenerateOrdersRequest(BaseModel):
    count: int = Field(ge=1, le=5000)
    date: Optional[str] = Field(None, pattern=r"^\d{4}-\d{2}-\d{2}$", description="Service date")
    window_start: str = Field(default="04:00", pattern=r"^\d{2}:\d{2}$")
    window_end: str = Field(default="10:00", pattern=r"^\d{2}:\d{2}$")
    distributions: Optional[Dict[str, Any]] = None

    class Config:
        extra = "forbid"


class GenerateOrdersResponse(BaseModel):
    orders_created: int = Field(ge=0)
    order_ids: List[str]

    class Config:
        extra = "forbid"


class ListOrdersQuery(BaseModel):
    status: Optional[OrderStatus] = None
    franchisee_id: Optional[str] = None
    created_after: Optional[datetime] = None
    created_before: Optional[datetime] = None
    limit: int = Field(default=100, ge=1, le=500)
    offset: int = Field(default=0, ge=0)

    class Config:
        extra = "forbid"


class ListOrdersResponse(BaseModel):
    total: int = Field(ge=0)
    orders: List[Order]

    class Config:
        extra = "forbid"


class LateOrderIntakeRequest(BaseModel):
    items: List[OrderItem] = Field(min_items=1)
    franchisee_id: str
    received_ts: datetime
    is_standalone_item: Optional[bool] = None

    class Config:
        extra = "forbid"


class LateOrderIntakeResponse(BaseModel):
    status: LateIntakeStatus
    order_id: str

    class Config:
        extra = "forbid"


# Mock data generators
def generate_mock_item() -> OrderItem:
    """Generate a mock order item"""
    items = [
        "BUN-SESAME-001", "PATTY-BEEF-QTR", "CHEESE-AMERICAN", "SAUCE-SPECIAL",
        "PICKLE-SLICED", "ONION-DICED", "LETTUCE-ICEBERG", "TOMATO-FRESH",
        "FRIES-MEDIUM", "DRINK-COKE-L", "NUGGETS-6PC", "SHAKE-VANILLA"
    ]
    
    return OrderItem(
        item_id=random.choice(items),
        qty=random.randint(1, 50),
        volume_cuft=round(random.uniform(0.1, 5.0), 2),
        non_substitutable=random.choice([True, False])
    )


def generate_mock_order(
    status: OrderStatus = OrderStatus.PENDING,
    window_start: str = "04:00",
    window_end: str = "10:00"
) -> Order:
    """Generate a mock order"""
    franchisees = ["FRAN_001", "FRAN_002", "FRAN_003", "FRAN_004", "FRAN_005"]
    
    return Order(
        id=f"ORD-{uuid.uuid4().hex[:8].upper()}",
        franchisee_id=random.choice(franchisees),
        created_ts=datetime.now(),
        window_start=window_start,
        window_end=window_end,
        status=status,
        notes=random.choice([None, "Special handling required", "Rush order", "Bulk delivery"]),
        items=[generate_mock_item() for _ in range(random.randint(1, 8))]
    )


# In-memory storage for demo purposes
mock_orders: Dict[str, Order] = {}