# Clean main.py with proper CORS configuration

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.config import settings
from app.database import engine, Base
import logging
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import models to register them with Base
from app.modules.refunds.models import Refund
from app.modules.activity_logs.models import ActivityLog
from app.modules.exchanges.models import Exchange
from app.modules.reviews.models import ProductReview
# from app.modules.categories.models import Category

# Import all routers
from app.modules.auth import routes as auth_routes
from app.modules.products import routes as product_routes
from app.modules.orders import routes as order_routes
from app.modules.users import routes as user_routes
from app.modules.delivery import routes as delivery_routes
from app.modules.refunds import routes as refund_routes
from app.modules.activity_logs import routes as activity_log_routes
from app.modules.settings import routes as settings_routes
from app.modules.exchanges import routes as exchange_routes
from app.modules.notifications import routes as notification_routes
from app.modules.cms.routes import router as cms_router
from app.modules.campaigns.routes import router as campaigns_router
from app.modules.b2b.routes import router as b2b_router
from app.modules.finance.routes import router as finance_router
from app.modules.reports.routes import router as reports_router
from app.modules.dashboard import routes as dashboard_routes
from app.modules.reviews import routes as reviews_routes
# from app.modules.categories.routes import router as categories_router

# Initialize FastAPI app
app = FastAPI(
    title="SevenXT Admin API",
    description="Backend API for SevenXT Admin Dashboard",
    version="2.0.0"
)

# ========================================
# CORS MIDDLEWARE (MUST BE FIRST!)
# ========================================
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # React frontend
        # "http://localhost:3001",  # React frontend (Vite alternate port)
        # "http://localhost:5173",  # Vite frontend
        "http://localhost:8001",  # Backend (for testing)
        # "http://192.168.29.146:3000", # Local LAN Access
        "https://sevenxt.in",  # Production Domain
        "https://www.sevenxt.in",  # Production Domain WWW
        "https://subconjunctively-unrebated-curtis.ngrok-free.dev",  # ngrok
        "https://sevenxt-dash.vercel.app",  # vercel
    ],
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods (GET, POST, PUT, DELETE, etc.)
    allow_headers=["*"],  # Allow all headers
)

# ========================================
# CUSTOM MIDDLEWARE FOR OPTIONS
# ========================================
@app.middleware("http")
async def allow_preflight_requests(request: Request, call_next):
    if request.method == "OPTIONS":
        return await call_next(request)
    return await call_next(request)

# ========================================
# STATIC FILES
# ========================================
# Create uploads directory
uploads_dir = "uploads"
os.makedirs(uploads_dir, exist_ok=True)
os.makedirs(f"{uploads_dir}/banners", exist_ok=True)
os.makedirs(f"{uploads_dir}/categories", exist_ok=True)
os.makedirs(f"{uploads_dir}/campaigns", exist_ok=True)
os.makedirs(f"{uploads_dir}/awb", exist_ok=True)

# Mount uploads directory
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# ========================================
# STARTUP EVENT
# ========================================
@app.on_event("startup")
async def startup_event():
    """Initialize database on startup"""
    try:
        # Create database tables
        Base.metadata.create_all(bind=engine)
        logger.info("✅ Database tables created/verified successfully")
        
        # Start background task for offer expiration
        import asyncio
        from app.modules.products.background_tasks import check_expired_offers
        asyncio.create_task(check_expired_offers())
        logger.info("✅ Background tasks started")
        
    except Exception as e:
        logger.error(f"❌ Startup error: {e}")
        logger.warning("Application started but database may not be available")

# ========================================
# REGISTER ALL ROUTERS
# ========================================
API_PREFIX = settings.API_V1_PREFIX

# Auth & Users
app.include_router(auth_routes.router, prefix=API_PREFIX)
app.include_router(user_routes.router, prefix=API_PREFIX)
app.include_router(user_routes.employees_router, prefix=API_PREFIX)

# Products & Orders
app.include_router(product_routes.router, prefix=API_PREFIX)
# app.include_router(categories_router, prefix=API_PREFIX)
app.include_router(order_routes.router, prefix=API_PREFIX)

# Delivery & Webhooks
app.include_router(delivery_routes.router, prefix=API_PREFIX)
app.include_router(delivery_routes.delivery_router, prefix=API_PREFIX)

# Refunds & Exchanges
app.include_router(refund_routes.router, prefix=API_PREFIX)
app.include_router(exchange_routes.router, prefix=API_PREFIX)

# CMS & Campaigns
app.include_router(cms_router, prefix=API_PREFIX)
app.include_router(campaigns_router, prefix=API_PREFIX)

# B2B & Finance
app.include_router(b2b_router, prefix=API_PREFIX)
app.include_router(finance_router, prefix=API_PREFIX)

# Reports & Dashboard
app.include_router(reports_router, prefix=API_PREFIX)
app.include_router(dashboard_routes.router, prefix=API_PREFIX)

# Notifications & Reviews
app.include_router(notification_routes.router, prefix=f"{API_PREFIX}/notifications")
app.include_router(reviews_routes.router, prefix=API_PREFIX)

# Activity Logs & Settings
app.include_router(activity_log_routes.router, prefix=API_PREFIX)
app.include_router(settings_routes.router, prefix=API_PREFIX)

# ========================================
# HEALTH CHECK ENDPOINTS
# ========================================
@app.get("/")
def root():
    return {
        "message": "SevenXT Admin API is running",
        "version": "2.0.0",
        "status": "healthy"
    }

@app.get("/health")
def health_check():
    return {"status": "healthy"}

# ========================================
# CORS TEST ENDPOINT
# ========================================
@app.get("/api/v1/test-cors")
def test_cors():
    """Test endpoint to verify CORS is working"""
    return {
        "message": "CORS is working!",
        "cors_enabled": True
    }
