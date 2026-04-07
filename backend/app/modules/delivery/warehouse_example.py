"""
Example: How to use warehouse fetching from Delhivery API with caching

This shows how to replace hardcoded warehouse addresses with 
addresses fetched from Delhivery API.
"""

from app.modules.delivery.warehouse_cache import get_cached_warehouse

# Example 1: Get warehouse details (cached)
warehouse = get_cached_warehouse("sevenxt")

print("Warehouse Details:")
print(f"Name: {warehouse['name']}")
print(f"Address: {warehouse['address']}")
print(f"City: {warehouse['city']}")
print(f"Pincode: {warehouse['pincode']}")
print(f"Phone: {warehouse['phone']}")

# Example 2: Use in return shipment
return_order_data = {
    # Destination: Your Warehouse (fetched from Delhivery)
    "customer_name": warehouse["name"],
    "address": warehouse["address"],
    "pincode": warehouse["pincode"],
    "city": warehouse["city"],
    "state": warehouse["state"],
    "phone": warehouse["phone"],
    "email": warehouse["email"],
    
    # Pickup Location: Customer's address
    "pickup_name": "Customer Name",
    "pickup_address": "Customer Address",
    # ... rest of customer details
}

# Example 3: The function is cached, so calling it again is instant
warehouse2 = get_cached_warehouse("sevenxt")  # Returns cached result (no API call)

print("\nSecond call (from cache):")
print(f"Address: {warehouse2['address']}")

# Example 4: Clear cache if needed (e.g., after updating warehouse in Delhivery)
from app.modules.delivery.warehouse_cache import clear_warehouse_cache
clear_warehouse_cache()  # Next call will fetch fresh data from Delhivery
