"""
API Routes Package

Contains all FastAPI router modules:
- auth_routes: Authentication endpoints
- vendors: Vendor CRUD endpoints
- products: Product CRUD endpoints
- purchase_orders: Purchase order endpoints
"""

from backend.routes.auth_routes import router as auth_router
from backend.routes.vendors import router as vendors_router
from backend.routes.products import router as products_router
from backend.routes.purchase_orders import router as purchase_orders_router

__all__ = [
    "auth_router",
    "vendors_router",
    "products_router",
    "purchase_orders_router"
]
