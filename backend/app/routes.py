from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from datetime import datetime, time
import random

from .models import (
    Order, OrderStatus, GenerateOrdersRequest, GenerateOrdersResponse,
    ListOrdersResponse, LateOrderIntakeRequest, LateOrderIntakeResponse,
    LateIntakeStatus, generate_mock_order, mock_orders
)
from seed_mcdonalds_inventory import get_db_connection
import psycopg2
import logging

logger = logging.getLogger(__name__)


def _ensure_orders_tables():
    """Create orders and order_items tables if they don't exist."""
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id TEXT PRIMARY KEY,
            franchisee_id TEXT,
            created_ts TIMESTAMP,
            window_start TEXT,
            window_end TEXT,
            status TEXT,
            notes TEXT
        )
        """)

        cur.execute("""
        CREATE TABLE IF NOT EXISTS order_items (
            id SERIAL PRIMARY KEY,
            order_id TEXT REFERENCES orders(id) ON DELETE CASCADE,
            item_id TEXT,
            qty NUMERIC,
            volume_cuft NUMERIC,
            non_substitutable BOOLEAN
        )
        """)

        conn.commit()
        cur.close()
    except Exception as e:
        logger.exception("Failed to ensure orders tables: %s", e)
    finally:
        if conn:
            conn.close()


# Ensure tables on import
_ensure_orders_tables()

router = APIRouter(prefix="/orders", tags=["orders"])


@router.post("/generate", response_model=GenerateOrdersResponse)
async def generate_orders(request: GenerateOrdersRequest):
    """Generate mock orders for testing purposes"""
    generated_ids = []
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        for _ in range(request.count):
            status = random.choice([
                OrderStatus.PENDING, OrderStatus.PLANNED, OrderStatus.LOCKED,
                OrderStatus.ROUTED, OrderStatus.DELIVERED
            ])
            order = generate_mock_order(
                status=status,
                window_start=request.window_start,
                window_end=request.window_end
            )

            # Persist to DB
            cur.execute(
                "INSERT INTO orders (id, franchisee_id, created_ts, window_start, window_end, status, notes) VALUES (%s,%s,%s,%s,%s,%s,%s)",
                (order.id, order.franchisee_id, order.created_ts, order.window_start, order.window_end, order.status.value, order.notes)
            )

            # Insert items
            for it in order.items:
                cur.execute(
                    "INSERT INTO order_items (order_id, item_id, qty, volume_cuft, non_substitutable) VALUES (%s,%s,%s,%s,%s)",
                    (order.id, it.item_id, it.qty, it.volume_cuft, it.non_substitutable)
                )

            generated_ids.append(order.id)

        conn.commit()
        cur.close()
    except Exception as e:
        logger.exception("Failed to persist generated orders: %s", e)
        raise HTTPException(status_code=500, detail="Failed to generate orders")
    finally:
        if conn:
            conn.close()

    # Also keep in-memory for backward compatibility - store minimal placeholders
    from .models import Order as OrderModel, OrderItem as OrderItemModel
    for oid in generated_ids:
        mock_orders[oid] = OrderModel(
            id=oid,
            franchisee_id="",
            created_ts=datetime.now(),
            window_start="00:00",
            window_end="00:00",
            status=OrderStatus.PENDING,
            notes=None,
            items=[OrderItemModel(item_id="PLACEHOLDER", qty=0, volume_cuft=0.0, non_substitutable=False)]
        )

    return GenerateOrdersResponse(orders_created=len(generated_ids), order_ids=generated_ids)


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
    
    # Query DB for orders
    conn = None
    results = []
    total = 0
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        where_clauses = []
        params = []
        if status:
            where_clauses.append("status = %s")
            params.append(status.value)
        if franchisee_id:
            where_clauses.append("franchisee_id = %s")
            params.append(franchisee_id)
        if created_after:
            where_clauses.append("created_ts >= %s")
            params.append(created_after)
        if created_before:
            where_clauses.append("created_ts <= %s")
            params.append(created_before)

        where_sql = " AND ".join(where_clauses)
        if where_sql:
            where_sql = "WHERE " + where_sql

        # Count total
        cur.execute(f"SELECT COUNT(*) FROM orders {where_sql}", tuple(params))
        cnt_row = cur.fetchone()
        total = cnt_row[0] if cnt_row and len(cnt_row) > 0 else 0

        # Fetch paginated
        cur.execute(f"SELECT id, franchisee_id, created_ts, window_start, window_end, status, notes FROM orders {where_sql} ORDER BY created_ts DESC LIMIT %s OFFSET %s", tuple(params + [limit, offset]))
        rows = cur.fetchall()

        for r in rows:
            oid, franchisee, created_ts, ws, we, st, notes = r
            # Fetch items
            cur.execute("SELECT item_id, qty, volume_cuft, non_substitutable FROM order_items WHERE order_id = %s", (oid,))
            items = []
            for it in cur.fetchall():
                item_id, qty, vol, non_sub = it
                items.append({"item_id": item_id, "qty": float(qty), "volume_cuft": float(vol) if vol is not None else 0.0, "non_substitutable": bool(non_sub)})

            # Build Order and its items
            from .models import OrderItem
            order_obj = Order(
                id=oid,
                franchisee_id=franchisee,
                created_ts=created_ts,
                window_start=ws,
                window_end=we,
                status=OrderStatus(st),
                notes=notes,
                items=[OrderItem(**it) for it in items]
            )
            results.append(order_obj)

        cur.close()
    except Exception as e:
        logger.exception("Failed to list orders: %s", e)
        raise HTTPException(status_code=500, detail="Failed to list orders")
    finally:
        if conn:
            conn.close()

    return ListOrdersResponse(total=total, orders=results)


@router.get("/{order_id}", response_model=Order)
async def get_order(order_id: str):
    """Get a specific order by ID"""
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT id, franchisee_id, created_ts, window_start, window_end, status, notes FROM orders WHERE id = %s", (order_id,))
        row = cur.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail=f"Order {order_id} not found")

        oid, franchisee, created_ts, ws, we, st, notes = row
        cur.execute("SELECT item_id, qty, volume_cuft, non_substitutable FROM order_items WHERE order_id = %s", (order_id,))
        items = [dict(item_id=r[0], qty=float(r[1]), volume_cuft=float(r[2]) if r[2] is not None else 0.0, non_substitutable=bool(r[3])) for r in cur.fetchall()]
        from .models import OrderItem
        order_obj = Order(id=oid, franchisee_id=franchisee, created_ts=created_ts, window_start=ws, window_end=we, status=OrderStatus(st), notes=notes, items=[OrderItem(**it) for it in items])
        cur.close()
        return order_obj
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Failed to fetch order %s: %s", order_id, e)
        raise HTTPException(status_code=500, detail="Failed to fetch order")
    finally:
        if conn:
            conn.close()


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
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("INSERT INTO orders (id, franchisee_id, created_ts, window_start, window_end, status, notes) VALUES (%s,%s,%s,%s,%s,%s,%s)", (order.id, order.franchisee_id, order.created_ts, order.window_start, order.window_end, order.status.value, order.notes))
        for it in order.items:
            cur.execute("INSERT INTO order_items (order_id, item_id, qty, volume_cuft, non_substitutable) VALUES (%s,%s,%s,%s,%s)", (order.id, it.item_id, it.qty, it.volume_cuft, it.non_substitutable))
        conn.commit()
        cur.close()
    except Exception as e:
        logger.exception("Failed to persist late intake order: %s", e)
        raise HTTPException(status_code=500, detail="Failed to persist late intake order")
    finally:
        if conn:
            conn.close()

    # keep in-memory reference
    mock_orders[order.id] = order

    return LateOrderIntakeResponse(status=status, order_id=order.id)