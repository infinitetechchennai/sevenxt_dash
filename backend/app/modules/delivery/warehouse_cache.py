"""
Warehouse Cache Service
Caches warehouse details from Delhivery to avoid repeated API calls
"""
from functools import lru_cache
from backend.app.modules.delivery.delhivery_client import delhivery_client


@lru_cache(maxsize=10)
def get_cached_warehouse(warehouse_name: str = "sevenxt") -> dict:
    """
    Get warehouse details with caching
    
    This function caches the result so we only call Delhivery API once.
    The cache persists until the server restarts.
    
    Args:
        warehouse_name: Name of the warehouse/pickup location in Delhivery
        
    Returns:
        dict: Warehouse details (address, phone, pincode, etc.)
    """
    return delhivery_client.get_warehouse_details(warehouse_name)


def clear_warehouse_cache():
    """Clear the warehouse cache (useful for testing or updates)"""
    get_cached_warehouse.cache_clear()
    print("[CACHE] Warehouse cache cleared")
