"""
Webhook Validation Script
Tests all webhook functionality and checks for errors
"""

import requests
import json

BASE_URL = "http://localhost:8001"

def print_section(title):
    print("\n" + "="*60)
    print(f"  {title}")
    print("="*60)

def test_webhook_endpoint():
    """Test if webhook endpoint is accessible"""
    print_section("TEST 1: Webhook Endpoint Accessibility")
    
    try:
        response = requests.get(f"{BASE_URL}/webhooks/test")
        print(f"✅ Status Code: {response.status_code}")
        print(f"✅ Response: {response.json()}")
        return True
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False

def test_simple_payload():
    """Test webhook with simple payload format"""
    print_section("TEST 2: Simple Payload Format")
    
    payload = {
        "waybill": "TEST_SIMPLE_123",
        "status": "Picked Up"
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/webhooks/delhivery/return",
            json=payload
        )
        print(f"Payload: {json.dumps(payload, indent=2)}")
        print(f"✅ Status Code: {response.status_code}")
        print(f"✅ Response: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False

def test_scans_array_payload():
    """Test webhook with scans array format"""
    print_section("TEST 3: Scans Array Payload Format")
    
    payload = {
        "waybill": "TEST_SCANS_456",
        "scans": [
            {
                "ScanDetail": {
                    "Scan": "In Transit",
                    "ScanDateTime": "2026-01-09 12:00:00",
                    "ScannedLocation": "Mumbai Hub"
                }
            },
            {
                "ScanDetail": {
                    "Scan": "Delivered",
                    "ScanDateTime": "2026-01-09 18:00:00",
                    "ScannedLocation": "Delhi Warehouse"
                }
            }
        ]
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/webhooks/delhivery/return",
            json=payload
        )
        print(f"Payload: {json.dumps(payload, indent=2)}")
        print(f"✅ Status Code: {response.status_code}")
        print(f"✅ Response: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False

def test_response_time():
    """Test webhook response time"""
    print_section("TEST 4: Response Time (<200ms)")
    
    import time
    
    payload = {
        "waybill": "TEST_SPEED_789",
        "status": "Picked Up"
    }
    
    times = []
    for i in range(5):
        try:
            start = time.time()
            response = requests.post(
                f"{BASE_URL}/webhooks/delhivery/return",
                json=payload
            )
            end = time.time()
            
            response_time = (end - start) * 1000
            times.append(response_time)
            print(f"  Test {i+1}: {response_time:.2f}ms - Status: {response.status_code}")
        except Exception as e:
            print(f"  Test {i+1}: ERROR - {e}")
    
    if times:
        avg_time = sum(times) / len(times)
        max_time = max(times)
        print(f"\n  Average: {avg_time:.2f}ms")
        print(f"  Max: {max_time:.2f}ms")
        
        if max_time < 200:
            print(f"  ✅ PASS - All responses < 200ms")
            return True
        else:
            print(f"  ❌ FAIL - Some responses > 200ms")
            return False
    return False

def test_missing_fields():
    """Test webhook with missing required fields"""
    print_section("TEST 5: Missing Fields Handling")
    
    # Test 1: Missing waybill
    print("\n  Test 5a: Missing waybill")
    payload = {"status": "Delivered"}
    try:
        response = requests.post(
            f"{BASE_URL}/webhooks/delhivery/return",
            json=payload
        )
        print(f"  Status Code: {response.status_code}")
        print(f"  Response: {response.json()}")
        if response.status_code == 200 and response.json().get("status") == "error":
            print(f"  ✅ Correctly handled missing waybill")
        else:
            print(f"  ⚠️ Unexpected response")
    except Exception as e:
        print(f"  ❌ ERROR: {e}")
    
    # Test 2: Missing status
    print("\n  Test 5b: Missing status")
    payload = {"waybill": "TEST123"}
    try:
        response = requests.post(
            f"{BASE_URL}/webhooks/delhivery/return",
            json=payload
        )
        print(f"  Status Code: {response.status_code}")
        print(f"  Response: {response.json()}")
        if response.status_code == 200 and response.json().get("status") == "error":
            print(f"  ✅ Correctly handled missing status")
        else:
            print(f"  ⚠️ Unexpected response")
    except Exception as e:
        print(f"  ❌ ERROR: {e}")
    
    return True

def test_exchange_webhook():
    """Test exchange webhook endpoint"""
    print_section("TEST 6: Exchange Webhook")
    
    payload = {
        "awb": "TEST_EXCHANGE_999",
        "status": "Delivered"
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/exchanges/webhook/delhivery",
            json=payload
        )
        print(f"Payload: {json.dumps(payload, indent=2)}")
        print(f"✅ Status Code: {response.status_code}")
        print(f"✅ Response: {response.json()}")
        return True
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False

def main():
    print("\n" + "🔍 WEBHOOK VALIDATION SCRIPT".center(60))
    print("Testing all webhook functionality...\n")
    
    results = {
        "Endpoint Accessibility": test_webhook_endpoint(),
        "Simple Payload": test_simple_payload(),
        "Scans Array Payload": test_scans_array_payload(),
        "Response Time": test_response_time(),
        "Missing Fields": test_missing_fields(),
        "Exchange Webhook": test_exchange_webhook()
    }
    
    # Summary
    print_section("SUMMARY")
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {test}: {status}")
    
    print(f"\n  Total: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n  🎉 ALL TESTS PASSED - No errors found!")
        print("  ✅ Webhooks are working correctly")
    else:
        print(f"\n  ⚠️ {total - passed} test(s) failed")
        print("  ❌ Please check the errors above")
    
    print("\n" + "="*60 + "\n")

if __name__ == "__main__":
    main()
