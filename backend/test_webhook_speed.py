import requests
import time

# Test webhook endpoint
url = "http://localhost:8001/webhooks/delhivery/return"

# Test payload
payload = {
    "waybill": "TEST123456",
    "status": "Picked Up"
}

# Measure response time
print("Testing webhook response time...")
print("-" * 50)

# Run 10 tests
times = []
for i in range(10):
    start = time.time()
    
    try:
        response = requests.post(url, json=payload)
        end = time.time()
        response_time = (end - start) * 1000  # Convert to milliseconds
        
        times.append(response_time)
        
        print(f"Test {i+1}: {response_time:.2f}ms - Status: {response.status_code}")
    except Exception as e:
        print(f"Test {i+1}: ERROR - {e}")

if times:
    print("-" * 50)
    print(f"Average: {sum(times)/len(times):.2f}ms")
    print(f"Min: {min(times):.2f}ms")
    print(f"Max: {max(times):.2f}ms")
    
    if max(times) < 200:
        print("✅ PASS - All responses < 200ms")
    else:
        print("❌ FAIL - Some responses > 200ms")
else:
    print("❌ No successful tests")
