import requests
import json
import time

# Test webhook endpoint
url = "http://localhost:8001/api/v1/exchanges/webhook/delhivery"
payload = {
    "waybill": "84927910000910",
    "status": "Attempt Fail"
}

print("=" * 60)
print("TESTING FAILED DELIVERY EMAIL ALERT")
print("=" * 60)
print(f"\nURL: {url}")
print(f"AWB: {payload['waybill']}")
print(f"Status: {payload['status']}")
print("\n" + "=" * 60)

for i in range(1, 4):
    print(f"\n🔄 Sending Attempt #{i}...")
    try:
        response = requests.post(url, json=payload)
        print(f"   Status Code: {response.status_code}")
        print(f"   Response: {response.json()}")
        
        if i == 3:
            print("\n" + "=" * 60)
            print("⚠️  THIS WAS THE 3RD ATTEMPT!")
            print("📧 Check your email: loguloges77@gmail.com")
            print("🔍 Check backend terminal for:")
            print("   - '🚨 CRITICAL: Return delivery failed 3 times'")
            print("   - '✅ Email sent successfully'")
            print("=" * 60)
        
        time.sleep(1)
    except Exception as e:
        print(f"   ❌ Error: {e}")

print("\n✅ Test complete!")
