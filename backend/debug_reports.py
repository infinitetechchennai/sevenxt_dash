
import requests
import json
import sys

# Since the backend is running on 8001
url = "http://localhost:8001/api/v1/reports/sales-inventory"

try:
    response = requests.get(url)
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"Items count: {len(data)}")
        if len(data) > 0:
            print("First item sample:")
            print(json.dumps(data[0], indent=2))
            
            # Check for totalRevenue existence and type
            has_revenue = all('totalRevenue' in item for item in data)
            print(f"All items have totalRevenue: {has_revenue}")
            
            # Check for valid numbers
            invalid_revenue_items = [item for item in data if not isinstance(item.get('totalRevenue'), (int, float))]
            if invalid_revenue_items:
                print(f"Items with invalid totalRevenue: {len(invalid_revenue_items)}")
                print(invalid_revenue_items[0])
            else:
                print("All totalRevenue fields are valid numbers.")
        else:
            print("Data is empty.")
    else:
        print(response.text)
except Exception as e:
    print(f"Error: {e}")
