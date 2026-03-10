"""
CRUD operations for ERP Purchase Order System.
Contains database operations for all entities.
"""

from datetime import datetime
from typing import List, Optional
import uuid
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import IntegrityError

from backend.models import User, Vendor, Product, PurchaseOrder, POItem, OrderStatus
from backend.schemas import (
    VendorCreate, VendorUpdate,
    ProductCreate, ProductUpdate,
    PurchaseOrderCreate, PurchaseOrderUpdate,
    UserCreate
)
from backend.config import settings


# =====================
# User CRUD Operations
# =====================

def get_user_by_email(db: Session, email: str) -> Optional[User]:
    """Get user by email address."""
    return db.query(User).filter(User.email == email).first()


def get_user_by_id(db: Session, user_id: int) -> Optional[User]:
    """Get user by ID."""
    return db.query(User).filter(User.id == user_id).first()


def create_user(db: Session, user: UserCreate) -> User:
    """Create a new user."""
    db_user = User(
        email=user.email,
        name=user.name,
        oauth_provider=user.oauth_provider
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def get_or_create_user(db: Session, email: str, name: str, oauth_provider: str = "google") -> User:
    """Get existing user or create new one. Updates name if changed."""
    user = get_user_by_email(db, email)
    if user:
        # Update name if it was empty or changed
        if name and (not user.name or user.name == "User" or user.name != name):
            user.name = name
            db.commit()
            db.refresh(user)
        return user
    
    user_data = UserCreate(email=email, name=name or "User", oauth_provider=oauth_provider)
    return create_user(db, user_data)


# =====================
# Vendor CRUD Operations
# =====================

def get_vendors(db: Session, skip: int = 0, limit: int = 100) -> List[Vendor]:
    """Get all vendors with pagination."""
    return db.query(Vendor).offset(skip).limit(limit).all()


def get_vendor_by_id(db: Session, vendor_id: int) -> Optional[Vendor]:
    """Get vendor by ID."""
    return db.query(Vendor).filter(Vendor.id == vendor_id).first()


def get_vendor_by_name(db: Session, name: str) -> Optional[Vendor]:
    """Get vendor by name."""
    return db.query(Vendor).filter(Vendor.name == name).first()


def create_vendor(db: Session, vendor: VendorCreate) -> Vendor:
    """Create a new vendor."""
    db_vendor = Vendor(
        name=vendor.name,
        contact_info=vendor.contact_info,
        rating=vendor.rating or 0.0
    )
    db.add(db_vendor)
    db.commit()
    db.refresh(db_vendor)
    return db_vendor


def update_vendor(db: Session, vendor_id: int, vendor: VendorUpdate) -> Optional[Vendor]:
    """Update an existing vendor."""
    db_vendor = get_vendor_by_id(db, vendor_id)
    if not db_vendor:
        return None
    
    # Update only provided fields
    update_data = vendor.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_vendor, field, value)
    
    db.commit()
    db.refresh(db_vendor)
    return db_vendor


def delete_vendor(db: Session, vendor_id: int) -> bool:
    """Delete a vendor by ID."""
    db_vendor = get_vendor_by_id(db, vendor_id)
    if not db_vendor:
        return False
    
    db.delete(db_vendor)
    db.commit()
    return True


# =====================
# Product CRUD Operations
# =====================

def get_products(db: Session, skip: int = 0, limit: int = 100) -> List[Product]:
    """Get all products with pagination."""
    return db.query(Product).offset(skip).limit(limit).all()


def get_product_by_id(db: Session, product_id: int) -> Optional[Product]:
    """Get product by ID."""
    return db.query(Product).filter(Product.id == product_id).first()


def get_product_by_sku(db: Session, sku: str) -> Optional[Product]:
    """Get product by SKU."""
    return db.query(Product).filter(Product.sku == sku).first()


def create_product(db: Session, product: ProductCreate) -> Product:
    """Create a new product."""
    db_product = Product(
        name=product.name,
        sku=product.sku,
        unit_price=product.unit_price,
        stock_level=product.stock_level or 0,
        description=product.description
    )
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    return db_product


def update_product(db: Session, product_id: int, product: ProductUpdate) -> Optional[Product]:
    """Update an existing product."""
    db_product = get_product_by_id(db, product_id)
    if not db_product:
        return None
    
    # Update only provided fields
    update_data = product.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_product, field, value)
    
    db.commit()
    db.refresh(db_product)
    return db_product


def delete_product(db: Session, product_id: int) -> bool:
    """Delete a product by ID."""
    db_product = get_product_by_id(db, product_id)
    if not db_product:
        return False
    
    db.delete(db_product)
    db.commit()
    return True


# =====================
# Purchase Order CRUD Operations
# =====================

def generate_reference_no() -> str:
    """Generate unique purchase order reference number."""
    timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    unique_part = str(uuid.uuid4())[:8].upper()
    return f"PO-{timestamp}-{unique_part}"


def calculate_order_totals(items: list) -> tuple:
    """
    Calculate order totals.
    Returns (subtotal, tax, total_amount)
    """
    subtotal = sum(item.quantity * item.price for item in items)
    tax = subtotal * settings.TAX_RATE
    total_amount = subtotal + tax
    return round(subtotal, 2), round(tax, 2), round(total_amount, 2)


def get_purchase_orders(db: Session, skip: int = 0, limit: int = 100) -> List[PurchaseOrder]:
    """Get all purchase orders with vendor info."""
    return db.query(PurchaseOrder)\
        .options(joinedload(PurchaseOrder.vendor))\
        .order_by(PurchaseOrder.created_at.desc())\
        .offset(skip)\
        .limit(limit)\
        .all()


def get_purchase_order_by_id(db: Session, po_id: int) -> Optional[PurchaseOrder]:
    """Get purchase order by ID with all related data."""
    return db.query(PurchaseOrder)\
        .options(
            joinedload(PurchaseOrder.vendor),
            joinedload(PurchaseOrder.items).joinedload(POItem.product)
        )\
        .filter(PurchaseOrder.id == po_id)\
        .first()


def get_purchase_order_by_reference(db: Session, reference_no: str) -> Optional[PurchaseOrder]:
    """Get purchase order by reference number."""
    return db.query(PurchaseOrder)\
        .filter(PurchaseOrder.reference_no == reference_no)\
        .first()


def create_purchase_order(db: Session, po: PurchaseOrderCreate) -> PurchaseOrder:
    """
    Create a new purchase order with items.
    Automatically calculates subtotal, tax, and total.
    """
    # Validate vendor exists
    vendor = get_vendor_by_id(db, po.vendor_id)
    if not vendor:
        raise ValueError(f"Vendor with id {po.vendor_id} not found")
    
    # Validate all products exist
    for item in po.items:
        product = get_product_by_id(db, item.product_id)
        if not product:
            raise ValueError(f"Product with id {item.product_id} not found")
    
    # Generate reference number
    reference_no = generate_reference_no()
    
    # Create PO items for calculation
    class TempItem:
        def __init__(self, quantity, price):
            self.quantity = quantity
            self.price = price
    
    temp_items = [TempItem(item.quantity, item.price) for item in po.items]
    subtotal, tax, total_amount = calculate_order_totals(temp_items)
    
    # Create purchase order
    db_po = PurchaseOrder(
        reference_no=reference_no,
        vendor_id=po.vendor_id,
        status=po.status or OrderStatus.DRAFT,
        subtotal=subtotal,
        tax=tax,
        total_amount=total_amount
    )
    db.add(db_po)
    db.flush()  # Get the PO ID
    
    # Create PO items
    for item in po.items:
        db_item = POItem(
            po_id=db_po.id,
            product_id=item.product_id,
            quantity=item.quantity,
            price=item.price
        )
        db.add(db_item)
    
    db.commit()
    db.refresh(db_po)
    
    # Reload with relationships
    return get_purchase_order_by_id(db, db_po.id)


def update_purchase_order(db: Session, po_id: int, po: PurchaseOrderUpdate) -> Optional[PurchaseOrder]:
    """Update an existing purchase order."""
    db_po = db.query(PurchaseOrder).filter(PurchaseOrder.id == po_id).first()
    if not db_po:
        return None
    
    # Validate vendor if being updated
    if po.vendor_id:
        vendor = get_vendor_by_id(db, po.vendor_id)
        if not vendor:
            raise ValueError(f"Vendor with id {po.vendor_id} not found")
    
    # Update only provided fields
    update_data = po.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_po, field, value)
    
    db.commit()
    db.refresh(db_po)
    return get_purchase_order_by_id(db, db_po.id)


def delete_purchase_order(db: Session, po_id: int) -> bool:
    """Delete a purchase order by ID."""
    db_po = db.query(PurchaseOrder).filter(PurchaseOrder.id == po_id).first()
    if not db_po:
        return False
    
    db.delete(db_po)
    db.commit()
    return True
