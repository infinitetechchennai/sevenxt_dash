import requests
import json

response = requests.get("http://localhost:8001/api/v1/dashboard/overview?timeframe=Monthly")
data = response.json()

print("📊 Dashboard API Response:\n")
print(f"Porter (Delivery Stats): {json.dumps(data.get('porter', []), indent=2)}")
