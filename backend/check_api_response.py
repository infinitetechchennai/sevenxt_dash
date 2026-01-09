import requests

try:
    response = requests.get("http://13.233.199.134/api/v1/products")
    response.raise_for_status()
    products = response.json()
    print(f"Fetched {len(products)} products.")
    for p in products:
        if p.get('rating', 0) > 0:
            print(f"Product: {p.get('name')}")
            print(f"  ID: {p.get('id')}")
            print(f"  Rating: {p.get('rating')}")
            print(f"  Reviews: {p.get('reviews')}")
            print(f"  LatestReview: '{p.get('latestReview')}'")
            print("-" * 20)
except Exception as e:
    print(f"Error: {e}")
