from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from datetime import datetime, time
import random

from .models import (
    Order, OrderStatus, GenerateOrdersRequest, GenerateOrdersResponse,
    ListOrdersResponse, LateOrderIntakeRequest, LateOrderIntakeResponse,
    LateIntakeStatus, generate_mock_order, mock_orders
)

router = APIRouter(prefix="/orders", tags=["orders"])


@router.post("/generate", response_model=GenerateOrdersResponse)
async def generate_orders(request: GenerateOrdersRequest):
    """Generate mock orders for testing purposes"""
    
    # Generate the requested number of orders
    generated_orders = []
    order_ids = []
    
    for _ in range(request.count):
        # Vary the status for more realistic mock data
        status = random.choice([
            OrderStatus.PENDING, OrderStatus.PLANNED, OrderStatus.LOCKED,
            OrderStatus.ROUTED, OrderStatus.DELIVERED
        ])
        
        order = generate_mock_order(
            status=status,
            window_start=request.window_start,
            window_end=request.window_end
        )
        
        # Store in mock database
        mock_orders[order.id] = order
        generated_orders.append(order)
        order_ids.append(order.id)
    
    return GenerateOrdersResponse(
        orders_created=len(generated_orders),
        order_ids=order_ids
    )


@router.get("", response_model=ListOrdersResponse)
async def list_orders(
    status: Optional[OrderStatus] = Query(None, description="Filter by order status"),
    franchisee_id: Optional[str] = Query(None, description="Filter by franchisee ID"),
    created_after: Optional[datetime] = Query(None, description="Filter orders created after this timestamp"),
    created_before: Optional[datetime] = Query(None, description="Filter orders created before this timestamp"),
    limit: int = Query(100, ge=1, le=500, description="Maximum number of orders to return"),
    offset: int = Query(0, ge=0, description="Number of orders to skip")
):
    """List orders with optional filtering"""
    
    # Start with all orders
    filtered_orders = list(mock_orders.values())
    
    # Apply filters
    if status:
        filtered_orders = [o for o in filtered_orders if o.status == status]
    
    if franchisee_id:
        filtered_orders = [o for o in filtered_orders if o.franchisee_id == franchisee_id]
    
    if created_after:
        filtered_orders = [o for o in filtered_orders if o.created_ts >= created_after]
    
    if created_before:
        filtered_orders = [o for o in filtered_orders if o.created_ts <= created_before]
    
    # Sort by created timestamp (newest first)
    filtered_orders.sort(key=lambda x: x.created_ts, reverse=True)
    
    # Apply pagination
    total = len(filtered_orders)
    paginated_orders = filtered_orders[offset:offset + limit]
    
    return ListOrdersResponse(
        total=total,
        orders=paginated_orders
    )


@router.get("/{order_id}", response_model=Order)
async def get_order(order_id: str):
    """Get a specific order by ID"""
    
    if order_id not in mock_orders:
        raise HTTPException(status_code=404, detail=f"Order {order_id} not found")
    
    return mock_orders[order_id]


@router.post("/late-intake", response_model=LateOrderIntakeResponse)
async def late_order_intake(request: LateOrderIntakeRequest):
    """Handle late order intake requests"""
    
    # Determine if this should be queued for next day or marked as exception
    # Mock logic: if received after 23:00 or is_standalone_item is True, queue for next day
    received_time = request.received_ts.time()
    cutoff_time = time(23, 0)  # 23:00
    
    if received_time >= cutoff_time or request.is_standalone_item:
        status = LateIntakeStatus.QUEUED_NEXT_DAY
        order_status = OrderStatus.QUEUED_NEXT_DAY
    else:
        # Random chance of exception for demo purposes
        if random.random() < 0.2:  # 20% chance of exception
            status = LateIntakeStatus.EXCEPTION
            order_status = OrderStatus.EXCEPTION
        else:
            status = LateIntakeStatus.QUEUED_NEXT_DAY
            order_status = OrderStatus.QUEUED_NEXT_DAY
    
    # Create an order from the late intake request
    order = Order(
        id=f"LATE-{datetime.now().strftime('%Y%m%d')}-{len(mock_orders) + 1:04d}",
        franchisee_id=request.franchisee_id,
        created_ts=request.received_ts,
        window_start="04:00",  # Default window for late orders
        window_end="10:00",
        status=order_status,
        notes="Late intake order",
        items=request.items
    )
    
    # Store the order
    mock_orders[order.id] = order
    
    return LateOrderIntakeResponse(
        status=status,
        order_id=order.id
    )