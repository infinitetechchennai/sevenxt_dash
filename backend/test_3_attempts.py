import requests
import json

url = "http://localhost:8001/api/v1/exchanges/webhook/delhivery"

print("\n" + "="*70)
print("SENDING 3 FAILED DELIVERY WEBHOOKS")
print("="*70)

for i in range(1, 4):
    payload = {
        "waybill": "84927910000910",
        "status": "Attempt Fail"
    }
    
    print(f"\n📤 Attempt {i}/3:")
    print(f"   Sending: {json.dumps(payload)}")
    
    try:
        response = requests.post(url, json=payload, timeout=5)
        print(f"   ✅ Response: {response.status_code}")
        print(f"   Body: {response.text[:200]}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    if i < 3:
        import time
        time.sleep(1)

print("\n" + "="*70)
print("✅ DONE! Check:")
print("1. Backend terminal for debug output")
print("2. Email: loguloges77@gmail.com")
print("3. Database: SELECT delivery_attempts FROM exchanges WHERE return_awb_number='84927910000910'")
print("="*70 + "\n")
