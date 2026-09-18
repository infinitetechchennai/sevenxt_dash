"""
Startup script for the backend server
"""
import uvicorn
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

if __name__ == "__main__":
    import os
    port = int(os.getenv("PORT", 8001))
    logger.info(f"Starting SevenXT Backend Server on port {port}...")
    logger.info("Configured for large file uploads (up to 100MB)")
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=port,
        reload=False,
        timeout_keep_alive=300,  # 5 minutes timeout for large uploads
        limit_max_requests=10000,  # Support many products
        limit_concurrency=1000,
        # Increase request body size to 100MB for bulk imports (5000+ products)
        h11_max_incomplete_event_size=100 * 1024 * 1024  # 100MB
    )
