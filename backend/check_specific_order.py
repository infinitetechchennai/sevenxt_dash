import requests
import json

try:
    url = "http://localhost:8001/api/v1/orders"
    print(f"Fetching orders from {url}...")
    
    response = requests.get(url)
    response.raise_for_status()
    orders = response.json()
    
    # Find the order with the specific AWB
    target_awb = "84927910001164"
    target_order = next((o for o in orders if o.get('awb_number') == target_awb), None)
    
    if target_order:
        print(f"\n✅ Found Order with AWB {target_awb}:")
        print(f"Order ID: {target_order.get('order_id')}")
        print(f"Amount: {target_order.get('amount')}")
        print(f"SGST Percentage: {target_order.get('sgst_percentage')}")
        print(f"CGST Percentage: {target_order.get('cgst_percentage')}")
        
        # Check raw logic
        sgst = target_order.get('sgst_percentage')
        if sgst is None or sgst == 0:
             print("\n⚠️ WARNING: GST for this order is 0 or None in the database!")
        else:
             print("\n✅ GST is present in API response.")
    else:
        print(f"\n❌ Order with AWB {target_awb} not found in the list.")
        # Print first 3 orders to see what's there
        print("First 3 orders:", [o.get('awb_number') for o in orders[:3]])

except Exception as e:
    print(f"Error: {e}")
