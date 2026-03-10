"""
Vendor API routes.
Handles CRUD operations for vendor management.
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.auth import get_current_user
from backend.models import User
from backend import crud
from backend.schemas import (
    VendorCreate, VendorUpdate, VendorResponse
)
from backend.security import limiter, sanitize, is_safe_input

router = APIRouter(prefix="/api/vendors", tags=["vendors"])


@router.get("", response_model=List[VendorResponse])
@limiter.limit("200/minute")
async def get_vendors(
    request: Request,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get all vendors.
    
    - **skip**: Number of records to skip (pagination)
    - **limit**: Maximum number of records to return
    """
    vendors = crud.get_vendors(db, skip=skip, limit=limit)
    return vendors


@router.get("/{vendor_id}", response_model=VendorResponse)
@limiter.limit("200/minute")
async def get_vendor(
    request: Request,
    vendor_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get a specific vendor by ID.
    
    - **vendor_id**: The ID of the vendor to retrieve
    """
    vendor = crud.get_vendor_by_id(db, vendor_id)
    if not vendor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Vendor with id {vendor_id} not found"
        )
    return vendor


@router.post("", response_model=VendorResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("30/minute")
async def create_vendor(
    request: Request,
    vendor: VendorCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new vendor.
    
    - **name**: Vendor name (required)
    - **contact_info**: Contact information (optional)
    - **rating**: Vendor rating 0-5 (optional)
    """
    # Validate input safety
    if not is_safe_input(vendor.name):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid characters detected in vendor name"
        )
    
    # Sanitize inputs
    vendor.name = sanitize(vendor.name, max_length=255)
    if vendor.contact_info:
        vendor.contact_info = sanitize(vendor.contact_info, max_length=1000)
    
    # Check if vendor with same name exists
    existing = crud.get_vendor_by_name(db, vendor.name)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Vendor with name '{vendor.name}' already exists"
        )
    
    return crud.create_vendor(db, vendor)


@router.put("/{vendor_id}", response_model=VendorResponse)
@limiter.limit("30/minute")
async def update_vendor(
    request: Request,
    vendor_id: int,
    vendor: VendorUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update an existing vendor.
    
    - **vendor_id**: The ID of the vendor to update
    - All fields are optional, only provided fields will be updated
    """
    # Sanitize inputs
    if vendor.name:
        if not is_safe_input(vendor.name):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid characters detected in vendor name"
            )
        vendor.name = sanitize(vendor.name, max_length=255)
    if vendor.contact_info:
        vendor.contact_info = sanitize(vendor.contact_info, max_length=1000)
    
    # Check if vendor exists
    existing = crud.get_vendor_by_id(db, vendor_id)
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Vendor with id {vendor_id} not found"
        )
    
    # Check for duplicate name if name is being updated
    if vendor.name and vendor.name != existing.name:
        duplicate = crud.get_vendor_by_name(db, vendor.name)
        if duplicate:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Vendor with name '{vendor.name}' already exists"
            )
    
    updated_vendor = crud.update_vendor(db, vendor_id, vendor)
    return updated_vendor


@router.delete("/{vendor_id}", status_code=status.HTTP_204_NO_CONTENT)
@limiter.limit("30/minute")
async def delete_vendor(
    request: Request,
    vendor_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Delete a vendor.
    
    - **vendor_id**: The ID of the vendor to delete
    
    Note: This will also delete all associated purchase orders.
    """
    success = crud.delete_vendor(db, vendor_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Vendor with id {vendor_id} not found"
        )
    return None
