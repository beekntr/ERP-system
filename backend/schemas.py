from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, EmailStr, Field
from enum import Enum


class OrderStatus(str, Enum):
    DRAFT = "draft"
    PENDING = "pending"
    APPROVED = "approved"
    ORDERED = "ordered"
    RECEIVED = "received"
    CANCELLED = "cancelled"


class UserBase(BaseModel):
    email: EmailStr
    name: str


class UserCreate(UserBase):
    oauth_provider: str = "google"


class UserResponse(UserBase):
    id: int
    oauth_provider: str
    created_at: datetime
    
    class Config:
        from_attributes = True


class VendorBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    contact_info: Optional[str] = None
    rating: Optional[float] = Field(default=0.0, ge=0.0, le=5.0)


class VendorCreate(VendorBase):
    pass


class VendorUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    contact_info: Optional[str] = None
    rating: Optional[float] = Field(None, ge=0.0, le=5.0)


class VendorResponse(VendorBase):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True


class ProductBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    sku: str = Field(..., min_length=1, max_length=100)
    unit_price: float = Field(..., ge=0.0)
    stock_level: Optional[int] = Field(default=0, ge=0)
    description: Optional[str] = None


class ProductCreate(ProductBase):
    pass


class ProductUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    sku: Optional[str] = Field(None, min_length=1, max_length=100)
    unit_price: Optional[float] = Field(None, ge=0.0)
    stock_level: Optional[int] = Field(None, ge=0)
    description: Optional[str] = None


class ProductResponse(ProductBase):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True


class POItemBase(BaseModel):
    product_id: int
    quantity: int = Field(..., gt=0)
    price: float = Field(..., ge=0.0)


class POItemCreate(POItemBase):
    pass


class POItemResponse(POItemBase):
    id: int
    po_id: int
    product: Optional[ProductResponse] = None
    
    class Config:
        from_attributes = True


class PurchaseOrderBase(BaseModel):
    vendor_id: int


class PurchaseOrderCreate(PurchaseOrderBase):
    items: List[POItemCreate] = Field(..., min_length=1)
    status: Optional[OrderStatus] = OrderStatus.DRAFT


class PurchaseOrderUpdate(BaseModel):
    vendor_id: Optional[int] = None
    status: Optional[OrderStatus] = None


class PurchaseOrderResponse(BaseModel):
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


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    email: Optional[str] = None
    user_id: Optional[int] = None


class GoogleAuthRequest(BaseModel):
    token: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class AIDescriptionRequest(BaseModel):
    product_name: str = Field(..., min_length=1, max_length=255)


class AIDescriptionResponse(BaseModel):
    description: str
