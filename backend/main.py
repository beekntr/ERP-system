"""
Main FastAPI application entry point.
ERP Purchase Order Management System.
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
import os

from backend.config import settings
from backend.database import init_db
from backend.security import limiter

# Import routers
from backend.routes.vendors import router as vendors_router
from backend.routes.products import router as products_router
from backend.routes.purchase_orders import router as purchase_orders_router
from backend.routes.auth_routes import router as auth_router

# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="""
    ## ERP Purchase Order Management System
    
    A mini ERP purchasing module for managing:
    - **Vendors** - Supplier management
    - **Products** - Product catalog and inventory
    - **Purchase Orders** - Order creation and tracking
    
    ### Features
    - Google OAuth authentication
    - JWT-based API security
    - Automatic tax calculation (5%)
    - AI-powered product descriptions (optional)
    - Rate limiting protection
    - Input sanitization
    
    ### Authentication
    All API endpoints (except /api/auth/*) require a valid JWT token.
    Include the token in the Authorization header:
    ```
    Authorization: Bearer <your_token>
    ```
    
    ### Rate Limits
    - Default: 100 requests/minute
    - Auth endpoints: 10 requests/minute
    - Create operations: 30 requests/minute
    """,
    docs_url="/api/docs" if settings.DEBUG else None,
    redoc_url="/api/redoc" if settings.DEBUG else None
)

# Add rate limiter to app state
app.state.limiter = limiter

# Add rate limit exceeded handler
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Security middleware for adding security headers
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    
    # Security headers
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    
    # Only add HSTS in production
    if not settings.DEBUG:
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    
    # Content Security Policy
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' https://accounts.google.com https://cdn.jsdelivr.net; "
        "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
        "img-src 'self' data: https:; "
        "font-src 'self' https://cdn.jsdelivr.net; "
        "connect-src 'self' https://accounts.google.com; "
        "frame-src https://accounts.google.com;"
    )
    
    return response

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8000", "http://127.0.0.1:8000"],  # Specific origins
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)

# Include API routers
app.include_router(auth_router)
app.include_router(vendors_router)
app.include_router(products_router)
app.include_router(purchase_orders_router)

# Get the base directory
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FRONTEND_DIR = os.path.join(BASE_DIR, "frontend")
STATIC_DIR = os.path.join(BASE_DIR, "static")

# Mount static files
if os.path.exists(STATIC_DIR):
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


# Serve frontend HTML files
@app.get("/")
async def serve_login():
    """Serve login page."""
    return FileResponse(os.path.join(FRONTEND_DIR, "login.html"))


@app.get("/login")
async def serve_login_page():
    """Serve login page."""
    return FileResponse(os.path.join(FRONTEND_DIR, "login.html"))


@app.get("/dashboard")
async def serve_dashboard():
    """Serve dashboard page."""
    return FileResponse(os.path.join(FRONTEND_DIR, "dashboard.html"))


@app.get("/vendors")
async def serve_vendors():
    """Serve vendors management page."""
    return FileResponse(os.path.join(FRONTEND_DIR, "vendors.html"))


@app.get("/products")
async def serve_products():
    """Serve products management page."""
    return FileResponse(os.path.join(FRONTEND_DIR, "products.html"))


@app.get("/create-po")
async def serve_create_po():
    """Serve create purchase order page."""
    return FileResponse(os.path.join(FRONTEND_DIR, "create_po.html"))


# Health check endpoint
@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION
    }


# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize database on startup."""
    print(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    print(f"Debug mode: {settings.DEBUG}")
    init_db()
    print("Database initialized successfully")


# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    print("Shutting down application...")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "backend.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG
    )
