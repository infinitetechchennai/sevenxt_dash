import requests
import json

try:
    # URL might be localhost:8001 or whatever the user is running
    # Based on previous context, it's port 8001
    url = "http://localhost:8001/api/v1/orders"
    print(f"Fetching from {url}...")
    
    response = requests.get(url)
    response.raise_for_status()
    
    orders = response.json()
    print(f"Total orders fetched: {len(orders)}")
    
    if orders:
        first_order = orders[0]
        print("\n--- First Order Payload ---")
        # Print relevant keys
        keys_to_check = ['id', 'order_id', 'amount', 'sgst_percentage', 'cgst_percentage']
        for k in keys_to_check:
            print(f"{k}: {first_order.get(k)}")
            
        # Check if any order has non-zero GST
        orders_with_gst = [o for o in orders if o.get('sgst_percentage') or o.get('cgst_percentage')]
        print(f"\nOrders with non-zero GST: {len(orders_with_gst)}")
        if orders_with_gst:
            print("Sample order with GST:", orders_with_gst[0].get('order_id'), 
                  "SGST:", orders_with_gst[0].get('sgst_percentage'))

except Exception as e:
    print(f"Error: {e}")
