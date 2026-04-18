# SevenXT Admin API — Main Application

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
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
from app.modules.orders.order_id_generator import OrderSequence  # noqa: F401 — ensures table is created

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

# Initialize FastAPI app
app = FastAPI(
    title="SevenXT Admin API",
    description="Backend API for SevenXT Admin Dashboard",
    version="2.0.0"
)

# ========================================
# CORS MIDDLEWARE (MUST BE FIRST!)
# Uses settings.CORS_ORIGINS as single source of truth
# ========================================
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Content-Disposition"],
)

# ========================================
# EXPLICIT PREFLIGHT HANDLER
# Ensures OPTIONS requests always get proper CORS headers
# even behind proxies/CDNs that may strip them
# ========================================
@app.middleware("http")
async def cors_preflight_handler(request: Request, call_next):
    if request.method == "OPTIONS":
        origin = request.headers.get("origin", "")
        if origin in settings.CORS_ORIGINS:
            return Response(
                status_code=200,
                headers={
                    "Access-Control-Allow-Origin": origin,
                    "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, PATCH, OPTIONS",
                    "Access-Control-Allow-Headers": "Content-Type, Authorization, X-Requested-With",
                    "Access-Control-Allow-Credentials": "true",
                    "Access-Control-Max-Age": "600",
                },
            )
    return await call_next(request)

# ========================================
# STATIC FILES
# Note: File uploads are now stored on Cloudinary.
# Local uploads/ directory is no longer used.
# ========================================
# Keep /static for temp PDFs (AWB labels, invoices) only
import os as _os
_os.makedirs("static/temp", exist_ok=True)
_os.makedirs("uploads", exist_ok=True)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")


# ========================================
# STARTUP EVENT
# ========================================
@app.on_event("startup")
async def startup_event():
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("✅ Database tables created/verified successfully")
        
        # FIX FOR LIVE RENDER DB: Add missing columns to b2b_applications
        try:
            from sqlalchemy import text
            with engine.begin() as conn:
                conn.execute(text("ALTER TABLE b2b_applications ADD COLUMN state VARCHAR(100);"))
                logger.info("✅ Added 'state' column to b2b_applications")
        except Exception as e:
            pass # Column already exists
            
        try:
            from sqlalchemy import text
            with engine.begin() as conn:
                conn.execute(text("ALTER TABLE b2b_applications ADD COLUMN registration_date VARCHAR(50);"))
                logger.info("✅ Added 'registration_date' column to b2b_applications")
        except Exception as e:
            pass # Column already exists

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

app.include_router(auth_routes.router, prefix=API_PREFIX)
app.include_router(user_routes.router, prefix=API_PREFIX)
app.include_router(user_routes.employees_router, prefix=API_PREFIX)

app.include_router(product_routes.router, prefix=API_PREFIX)
app.include_router(order_routes.router, prefix=API_PREFIX)

app.include_router(delivery_routes.router, prefix=API_PREFIX)
app.include_router(delivery_routes.delivery_router, prefix=API_PREFIX)

app.include_router(refund_routes.router, prefix=API_PREFIX)
app.include_router(exchange_routes.router, prefix=API_PREFIX)

app.include_router(cms_router, prefix=API_PREFIX)
app.include_router(campaigns_router, prefix=API_PREFIX)

app.include_router(b2b_router, prefix=API_PREFIX)
app.include_router(finance_router, prefix=API_PREFIX)

app.include_router(reports_router, prefix=API_PREFIX)
app.include_router(dashboard_routes.router, prefix=API_PREFIX)

app.include_router(notification_routes.router, prefix=f"{API_PREFIX}/notifications")
app.include_router(reviews_routes.router, prefix=API_PREFIX)

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
