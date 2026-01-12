
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.config import settings
from app.modules.auth import routes as auth_routes
from app.database import engine, Base
import logging
import os


# Import models to register them with Base
from app.modules.refunds.models import Refund
from app.modules.activity_logs.models import ActivityLog
from app.modules.exchanges.models import Exchange
<<<<<<< HEAD
from app.modules.reviews.models import ProductReview
=======
>>>>>>> 18b14a9a377cc9a7ca746e390bd3e86ba8561ad7

# --- IMPORT ALL ROUTERS (Verified) ---
from app.modules.auth import routes as auth_routes
from app.modules.products import routes as product_routes
from app.modules.cms.routes import router as cms_router
from app.modules.campaigns.routes import router as campaigns_router
from app.modules.b2b.routes import router as b2b_router # B2B Router
from app.modules.finance.routes import router as finance_router 
<<<<<<< HEAD
from app.modules.reports.routes import router as reports_router
from app.modules.dashboard import routes as dashboard_routes
from app.modules.notifications.routes import router as notifications_router
from app.modules.reviews import routes as reviews_routes
=======
>>>>>>> 18b14a9a377cc9a7ca746e390bd3e86ba8561ad7
# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)




# 2. APP INITIALIZATION
# Single initialization is mandatory to prevent 404 errors on your routes

app = FastAPI(
    title="SevenXT Admin API",
    description="Backend API for SevenXT Admin Dashboard",
    version="2.0.0"
)

<<<<<<< HEAD
# Mount uploads directory for serving profile pictures
from pathlib import Path
uploads_dir = Path("uploads")
uploads_dir.mkdir(exist_ok=True)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

=======
>>>>>>> 18b14a9a377cc9a7ca746e390bd3e86ba8561ad7

@app.on_event("startup")
async def startup_event():
    """Initialize database on startup"""
    try:
        # Create database tables (only if they don't exist)
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created/verified successfully")
        
        # Start background task to check expired offers
        import asyncio
        from app.modules.products.background_tasks import check_expired_offers
        asyncio.create_task(check_expired_offers())
        logger.info("Started background task for offer expiration")
        
    except Exception as e:
        logger.error(f"Failed to connect to database: {e}")
        logger.warning("Application started but database is not available. Please ensure MySQL is running.")

<<<<<<< HEAD
=======
# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",   # React
        "http://localhost:5173",   # Vite (just in case)
    ],
)
>>>>>>> 18b14a9a377cc9a7ca746e390bd3e86ba8561ad7
# 3. DIRECTORY SETUP
# Automatically creates folders for your CMS and B2B uploads
upload_dirs = ["uploads", "uploads/banners", "uploads/categories", "uploads/campaigns"]
for folder in upload_dirs:
    os.makedirs(folder, exist_ok=True)

# 4. STATIC FILES MOUNTING
# This allows your dashboard to show the GST/PAN certificates
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# 5. CORS MIDDLEWARE
app.add_middleware(
    CORSMiddleware,
<<<<<<< HEAD
    allow_origins=settings.CORS_ORIGINS or [
        "http://13.233.199.134", 
        "http://localhost:3001",  # Added for frontend on port 3001
        "http://localhost:5173"
    ],
=======
    allow_origins=settings.CORS_ORIGINS or ["http://localhost:3000", "http://localhost:5173"],

>>>>>>> 18b14a9a377cc9a7ca746e390bd3e86ba8561ad7
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from app.modules.products import routes as product_routes
from app.modules.orders import routes as order_routes

# Include Routers
app.include_router(auth_routes.router, prefix=settings.API_V1_PREFIX)

from app.modules.users import routes as user_routes
app.include_router(user_routes.router, prefix=settings.API_V1_PREFIX)
app.include_router(user_routes.employees_router, prefix=settings.API_V1_PREFIX)

app.include_router(product_routes.router, prefix=settings.API_V1_PREFIX)
app.include_router(order_routes.router, prefix=settings.API_V1_PREFIX)

from app.modules.delivery import routes as delivery_routes
app.include_router(delivery_routes.router, prefix=settings.API_V1_PREFIX)  # Webhook router
app.include_router(delivery_routes.delivery_router, prefix=settings.API_V1_PREFIX)  # Delivery operations router

from app.modules.refunds import routes as refund_routes
app.include_router(refund_routes.router, prefix=settings.API_V1_PREFIX)

from app.modules.activity_logs import routes as activity_log_routes
app.include_router(activity_log_routes.router, prefix=settings.API_V1_PREFIX)

from app.modules.settings import routes as settings_routes
app.include_router(settings_routes.router, prefix=settings.API_V1_PREFIX)

from app.modules.exchanges import routes as exchange_routes
app.include_router(exchange_routes.router, prefix=settings.API_V1_PREFIX)

# WEBHOOK ROUTES (for Delhivery status updates)
# These endpoints receive automatic status updates when delivery boy scans AWB
from app.modules.refunds import webhooks as refund_webhooks
app.include_router(refund_webhooks.router)

from app.modules.exchanges import webhooks as exchange_webhooks
app.include_router(exchange_webhooks.router)

from app.modules.notifications import routes as notification_routes
app.include_router(notification_routes.router, prefix=settings.API_V1_PREFIX + "/notifications")

from fastapi.staticfiles import StaticFiles
import os
os.makedirs("uploads", exist_ok=True)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# Include Routers
app.include_router(auth_routes.router, prefix=settings.API_V1_PREFIX)
app.include_router(product_routes.router, prefix=settings.API_V1_PREFIX)

# 6. CUSTOM MIDDLEWARE (Ensures OPTIONS requests work for B2B/Finance)
@app.middleware("http")
async def allow_preflight_requests(request: Request, call_next):
    if request.method == "OPTIONS":
        return await call_next(request)
    return await call_next(request)

# 7. STARTUP EVENT
@app.on_event("startup")
async def startup_event():
    try:
        # Verifies database tables (CMS, B2B, Products, etc.)
        Base.metadata.create_all(bind=engine)
        logger.info("✅ Database tables verified")

        # Background task for offer expiration
        import asyncio
        from app.modules.products.background_tasks import check_expired_offers
        asyncio.create_task(check_expired_offers())
        logger.info("✅ Background tasks started")

    except Exception as e:
        logger.error(f"❌ Startup error: {e}")

# -------------------------------------------------
# 8. REGISTER ALL ROUTERS (All Workflows Preserved)
# -------------------------------------------------
API_PREFIX = settings.API_V1_PREFIX 

# Auth & Employee Workflows
app.include_router(auth_routes.router, prefix=API_PREFIX)

# Product & Inventory Workflows
app.include_router(product_routes.router, prefix=API_PREFIX)

# CMS & Campaign Workflows
app.include_router(cms_router, prefix=API_PREFIX)
app.include_router(campaigns_router, prefix=API_PREFIX)

# B2B MANAGEMENT WORKFLOW (Updated with Auto-Verify)
app.include_router(b2b_router, prefix=API_PREFIX) 

# FINANCE & PAYMENTS WORKFLOW
app.include_router(finance_router, prefix=API_PREFIX)
# REPORTS WORKFLOW 
app.include_router(reports_router, prefix=API_PREFIX)

# NOTIFICATIONS WORKFLOW
app.include_router(notifications_router, prefix=API_PREFIX)

# DASHBOARD WORKFLOW
app.include_router(dashboard_routes.router, prefix=settings.API_V1_PREFIX)

# PRODUCT REVIEWS
app.include_router(reviews_routes.router, prefix=settings.API_V1_PREFIX)
# -------------------------------------------------
# 9. SYSTEM HEALTH
# -------------------------------------------------

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
