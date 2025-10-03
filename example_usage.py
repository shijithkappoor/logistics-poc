"""
Example usage of the Pydantic models for Orders API

Run this after installing pydantic:
pip install pydantic

"""

from datetime import datetime
from models import (
    OrderItem, Order, OrderStatus,
    GenerateOrdersRequest, GenerateOrdersResponse,
    ListOrdersQuery, ListOrdersResponse,
    LateOrderIntakeRequest, LateOrderIntakeResponse, LateOrderIntakeStatus
)


def example_usage():
    """Demonstrate usage of the Pydantic models"""
    
    # Create order items
    item1 = OrderItem(
        item_id="ITEM001",
        qty=2.5,
        volume_cuft=1.2,
        non_substitutable=True
    )
    
    item2 = OrderItem(
        item_id="ITEM002", 
        qty=1.0,
        volume_cuft=0.8,
        non_substitutable=False
    )
    
    # Create an order
    order = Order(
        id="ORDER123",
        franchisee_id="FRANCHISE001",
        created_ts=datetime.now(),
        window_start="04:00",
        window_end="10:00", 
        status=OrderStatus.PENDING,
        notes="Rush delivery",
        items=[item1, item2]
    )
    
    print("Created Order:", order.model_dump_json(indent=2))
    
    # Generate orders request
    generate_request = GenerateOrdersRequest(
        count=10,
        date="2025-10-03",
        window_start="05:00",
        window_end="11:00"
    )
    
    print("\nGenerate Orders Request:", generate_request.model_dump_json(indent=2))
    
    # Generate orders response
    generate_response = GenerateOrdersResponse(
        orders_created=10,
        order_ids=["ORDER001", "ORDER002", "ORDER003"]
    )
    
    print("\nGenerate Orders Response:", generate_response.model_dump_json(indent=2))
    
    # List orders query
    list_query = ListOrdersQuery(
        status=OrderStatus.PENDING,
        franchisee_id="FRANCHISE001",
        limit=50,
        offset=0
    )
    
    print("\nList Orders Query:", list_query.model_dump_json(indent=2))
    
    # List orders response
    list_response = ListOrdersResponse(
        total=1,
        orders=[order]
    )
    
    print("\nList Orders Response:", list_response.model_dump_json(indent=2))
    
    # Late order intake request
    late_intake_request = LateOrderIntakeRequest(
        items=[item1],
        franchisee_id="FRANCHISE001",
        received_ts=datetime.now(),
        is_standalone_item=True
    )
    
    print("\nLate Order Intake Request:", late_intake_request.model_dump_json(indent=2))
    
    # Late order intake response
    late_intake_response = LateOrderIntakeResponse(
        status=LateOrderIntakeStatus.QUEUED_NEXT_DAY,
        order_id="ORDER124"
    )
    
    print("\nLate Order Intake Response:", late_intake_response.model_dump_json(indent=2))


if __name__ == "__main__":
    example_usage()