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

from backend.routes.vendors import router as vendors_router
from backend.routes.products import router as products_router
from backend.routes.purchase_orders import router as purchase_orders_router
from backend.routes.auth_routes import router as auth_router

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="ERP Purchase Order Management System",
    docs_url="/api/docs" if settings.DEBUG else None,
    redoc_url="/api/redoc" if settings.DEBUG else None
)

app.state.limiter = limiter

app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    
    if not settings.DEBUG:
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    
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

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8000", "http://127.0.0.1:8000"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)

app.include_router(auth_router)
app.include_router(vendors_router)
app.include_router(products_router)
app.include_router(purchase_orders_router)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FRONTEND_DIR = os.path.join(BASE_DIR, "frontend")
STATIC_DIR = os.path.join(BASE_DIR, "static")

if os.path.exists(STATIC_DIR):
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/")
async def serve_login():
    return FileResponse(os.path.join(FRONTEND_DIR, "login.html"))


@app.get("/login")
async def serve_login_page():
    return FileResponse(os.path.join(FRONTEND_DIR, "login.html"))


@app.get("/dashboard")
async def serve_dashboard():
    return FileResponse(os.path.join(FRONTEND_DIR, "dashboard.html"))


@app.get("/vendors")
async def serve_vendors():
    return FileResponse(os.path.join(FRONTEND_DIR, "vendors.html"))


@app.get("/products")
async def serve_products():
    return FileResponse(os.path.join(FRONTEND_DIR, "products.html"))


@app.get("/create-po")
async def serve_create_po():
    return FileResponse(os.path.join(FRONTEND_DIR, "create_po.html"))


@app.get("/api/health")
async def health_check():
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION
    }


@app.on_event("startup")
async def startup_event():
    print(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    print(f"Debug mode: {settings.DEBUG}")
    init_db()
    print("Database initialized successfully")


@app.on_event("shutdown")
async def shutdown_event():
    print("Shutting down application...")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "backend.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG
    )
