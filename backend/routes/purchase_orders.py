"""
Purchase Order API routes.
Handles CRUD operations for purchase order management.
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.auth import get_current_user
from backend.models import User
from backend import crud
from backend.schemas import (
    PurchaseOrderCreate, PurchaseOrderUpdate,
    PurchaseOrderResponse, PurchaseOrderListResponse
)
from backend.security import limiter

router = APIRouter(prefix="/api/purchase-orders", tags=["purchase-orders"])


@router.get("", response_model=List[PurchaseOrderListResponse])
@limiter.limit("200/minute")
async def get_purchase_orders(
    request: Request,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get all purchase orders.
    
    - **skip**: Number of records to skip (pagination)
    - **limit**: Maximum number of records to return
    
    Returns purchase orders with vendor info (without line items for performance).
    """
    purchase_orders = crud.get_purchase_orders(db, skip=skip, limit=limit)
    return purchase_orders


@router.get("/{po_id}", response_model=PurchaseOrderResponse)
@limiter.limit("200/minute")
async def get_purchase_order(
    request: Request,
    po_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get a specific purchase order by ID.
    
    - **po_id**: The ID of the purchase order to retrieve
    
    Returns full purchase order with vendor details and all line items.
    """
    po = crud.get_purchase_order_by_id(db, po_id)
    if not po:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Purchase order with id {po_id} not found"
        )
    return po


@router.post("", response_model=PurchaseOrderResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("30/minute")
async def create_purchase_order(
    request: Request,
    po: PurchaseOrderCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new purchase order.
    
    Request body:
    - **vendor_id**: ID of the vendor (required)
    - **items**: List of line items (required, at least 1)
        - **product_id**: ID of the product
        - **quantity**: Quantity ordered (must be > 0)
        - **price**: Unit price
    - **status**: Order status (optional, defaults to 'draft')
    
    The system automatically calculates:
    - **subtotal**: Sum of (quantity × price) for all items
    - **tax**: 5% of subtotal
    - **total_amount**: subtotal + tax
    
    Example request:
    ```json
    {
        "vendor_id": 1,
        "items": [
            {"product_id": 1, "quantity": 3, "price": 120},
            {"product_id": 2, "quantity": 5, "price": 80}
        ]
    }
    ```
    """
    try:
        created_po = crud.create_purchase_order(db, po)
        return created_po
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.put("/{po_id}", response_model=PurchaseOrderResponse)
@limiter.limit("30/minute")
async def update_purchase_order(
    request: Request,
    po_id: int,
    po: PurchaseOrderUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update an existing purchase order.
    
    - **po_id**: The ID of the purchase order to update
    - **vendor_id**: New vendor ID (optional)
    - **status**: New status (optional)
    
    Note: This endpoint updates only the order header.
    To modify line items, delete and recreate the order.
    """
    existing = crud.get_purchase_order_by_id(db, po_id)
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Purchase order with id {po_id} not found"
        )
    
    try:
        updated_po = crud.update_purchase_order(db, po_id, po)
        return updated_po
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.delete("/{po_id}", status_code=status.HTTP_204_NO_CONTENT)
@limiter.limit("30/minute")
async def delete_purchase_order(
    request: Request,
    po_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Delete a purchase order.
    
    - **po_id**: The ID of the purchase order to delete
    
    This will also delete all associated line items.
    """
    success = crud.delete_purchase_order(db, po_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Purchase order with id {po_id} not found"
        )
    return None
