"""
SQLAlchemy ORM Models for ERP Purchase Order System.
Defines all database tables and relationships.
"""

from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Float, DateTime, 
    ForeignKey, Text, Enum as SQLEnum
)
from sqlalchemy.orm import relationship
import enum

from backend.database import Base


class OrderStatus(str, enum.Enum):
    """Enumeration for purchase order status."""
    DRAFT = "draft"
    PENDING = "pending"
    APPROVED = "approved"
    ORDERED = "ordered"
    RECEIVED = "received"
    CANCELLED = "cancelled"


class User(Base):
    """
    User model for authentication.
    Stores user information from OAuth providers.
    """
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    name = Column(String(255), nullable=False)
    oauth_provider = Column(String(50), default="google")
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<User(id={self.id}, email={self.email})>"


class Vendor(Base):
    """
    Vendor model for supplier management.
    Stores vendor/supplier information.
    """
    __tablename__ = "vendors"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    contact_info = Column(Text, nullable=True)
    rating = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship to purchase orders
    purchase_orders = relationship("PurchaseOrder", back_populates="vendor", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Vendor(id={self.id}, name={self.name})>"


class Product(Base):
    """
    Product model for inventory management.
    Stores product information including SKU and pricing.
    """
    __tablename__ = "products"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    sku = Column(String(100), unique=True, nullable=False, index=True)
    unit_price = Column(Float, nullable=False, default=0.0)
    stock_level = Column(Integer, default=0)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship to purchase order items
    po_items = relationship("POItem", back_populates="product")
    
    def __repr__(self):
        return f"<Product(id={self.id}, name={self.name}, sku={self.sku})>"


class PurchaseOrder(Base):
    """
    Purchase Order model.
    Stores order header information including totals and status.
    """
    __tablename__ = "purchase_orders"
    
    id = Column(Integer, primary_key=True, index=True)
    reference_no = Column(String(50), unique=True, nullable=False, index=True)
    vendor_id = Column(Integer, ForeignKey("vendors.id"), nullable=False)
    order_date = Column(DateTime, default=datetime.utcnow)
    status = Column(SQLEnum(OrderStatus), default=OrderStatus.DRAFT)
    subtotal = Column(Float, default=0.0)
    tax = Column(Float, default=0.0)
    total_amount = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    vendor = relationship("Vendor", back_populates="purchase_orders")
    items = relationship("POItem", back_populates="purchase_order", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<PurchaseOrder(id={self.id}, reference_no={self.reference_no})>"


class POItem(Base):
    """
    Purchase Order Item model.
    Stores individual line items in a purchase order.
    """
    __tablename__ = "po_items"
    
    id = Column(Integer, primary_key=True, index=True)
    po_id = Column(Integer, ForeignKey("purchase_orders.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    quantity = Column(Integer, nullable=False, default=1)
    price = Column(Float, nullable=False)
    
    # Relationships
    purchase_order = relationship("PurchaseOrder", back_populates="items")
    product = relationship("Product", back_populates="po_items")
    
    @property
    def line_total(self):
        """Calculate line item total (quantity × price)."""
        return self.quantity * self.price
    
    def __repr__(self):
        return f"<POItem(id={self.id}, po_id={self.po_id}, product_id={self.product_id})>"
