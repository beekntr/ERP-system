"""
Pydantic schemas for request/response validation.
Defines data transfer objects (DTOs) for API endpoints.
"""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, EmailStr, Field
from enum import Enum


class OrderStatus(str, Enum):
    """Enumeration for purchase order status."""
    DRAFT = "draft"
    PENDING = "pending"
    APPROVED = "approved"
    ORDERED = "ordered"
    RECEIVED = "received"
    CANCELLED = "cancelled"


# =====================
# User Schemas
# =====================

class UserBase(BaseModel):
    """Base user schema with common fields."""
    email: EmailStr
    name: str


class UserCreate(UserBase):
    """Schema for creating a new user."""
    oauth_provider: str = "google"


class UserResponse(UserBase):
    """Schema for user response."""
    id: int
    oauth_provider: str
    created_at: datetime
    
    class Config:
        from_attributes = True


# =====================
# Vendor Schemas
# =====================

class VendorBase(BaseModel):
    """Base vendor schema with common fields."""
    name: str = Field(..., min_length=1, max_length=255)
    contact_info: Optional[str] = None
    rating: Optional[float] = Field(default=0.0, ge=0.0, le=5.0)


class VendorCreate(VendorBase):
    """Schema for creating a new vendor."""
    pass


class VendorUpdate(BaseModel):
    """Schema for updating a vendor."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    contact_info: Optional[str] = None
    rating: Optional[float] = Field(None, ge=0.0, le=5.0)


class VendorResponse(VendorBase):
    """Schema for vendor response."""
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True


# =====================
# Product Schemas
# =====================

class ProductBase(BaseModel):
    """Base product schema with common fields."""
    name: str = Field(..., min_length=1, max_length=255)
    sku: str = Field(..., min_length=1, max_length=100)
    unit_price: float = Field(..., ge=0.0)
    stock_level: Optional[int] = Field(default=0, ge=0)
    description: Optional[str] = None


class ProductCreate(ProductBase):
    """Schema for creating a new product."""
    pass


class ProductUpdate(BaseModel):
    """Schema for updating a product."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    sku: Optional[str] = Field(None, min_length=1, max_length=100)
    unit_price: Optional[float] = Field(None, ge=0.0)
    stock_level: Optional[int] = Field(None, ge=0)
    description: Optional[str] = None


class ProductResponse(ProductBase):
    """Schema for product response."""
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True


# =====================
# Purchase Order Item Schemas
# =====================

class POItemBase(BaseModel):
    """Base PO item schema."""
    product_id: int
    quantity: int = Field(..., gt=0)
    price: float = Field(..., ge=0.0)


class POItemCreate(POItemBase):
    """Schema for creating a PO item."""
    pass


class POItemResponse(POItemBase):
    """Schema for PO item response."""
    id: int
    po_id: int
    product: Optional[ProductResponse] = None
    
    class Config:
        from_attributes = True


# =====================
# Purchase Order Schemas
# =====================

class PurchaseOrderBase(BaseModel):
    """Base purchase order schema."""
    vendor_id: int


class PurchaseOrderCreate(PurchaseOrderBase):
    """Schema for creating a purchase order."""
    items: List[POItemCreate] = Field(..., min_length=1)
    status: Optional[OrderStatus] = OrderStatus.DRAFT


class PurchaseOrderUpdate(BaseModel):
    """Schema for updating a purchase order."""
    vendor_id: Optional[int] = None
    status: Optional[OrderStatus] = None


class PurchaseOrderResponse(BaseModel):
    """Schema for purchase order response."""
    id: int
    reference_no: str
    vendor_id: int
    order_date: datetime
    status: OrderStatus
    subtotal: float
    tax: float
    total_amount: float
    created_at: datetime
    vendor: Optional[VendorResponse] = None
    items: List[POItemResponse] = []
    
    class Config:
        from_attributes = True


class PurchaseOrderListResponse(BaseModel):
    """Schema for purchase order list response (without items)."""
    id: int
    reference_no: str
    vendor_id: int
    order_date: datetime
    status: OrderStatus
    subtotal: float
    tax: float
    total_amount: float
    created_at: datetime
    vendor: Optional[VendorResponse] = None
    
    class Config:
        from_attributes = True


# =====================
# Authentication Schemas
# =====================

class Token(BaseModel):
    """JWT token response schema."""
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Token payload data schema."""
    email: Optional[str] = None
    user_id: Optional[int] = None


class GoogleAuthRequest(BaseModel):
    """Google OAuth token request schema."""
    token: str


class LoginResponse(BaseModel):
    """Login response with user info and token."""
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


# =====================
# AI Description Schema
# =====================

class AIDescriptionRequest(BaseModel):
    """Request schema for AI-generated product description."""
    product_name: str = Field(..., min_length=1, max_length=255)


class AIDescriptionResponse(BaseModel):
    """Response schema for AI-generated product description."""
    description: str
