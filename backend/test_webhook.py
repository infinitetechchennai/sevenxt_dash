import requests
import json

# Test webhook endpoint
url = "http://localhost:8001/api/v1/exchanges/webhook/delhivery"
payload = {
    "waybill": "84927910000910",
    "status": "Attempt Fail"
}

print("Sending webhook request...")
print(f"URL: {url}")
print(f"Payload: {json.dumps(payload, indent=2)}")
print("-" * 50)

try:
    response = requests.post(url, json=payload)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")
except Exception as e:
    print(f"Error: {e}")
