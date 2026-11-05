"""
Test script to verify all dashboard APIs are working
"""
import requests
import json

BASE_URL = "http://localhost:8000"

def test_api(endpoint, method="GET", data=None):
    """Test an API endpoint"""
    url = f"{BASE_URL}{endpoint}"
    try:
        if method == "GET":
            response = requests.get(url, timeout=5)
        else:
            response = requests.post(url, json=data, timeout=5)
        
        print(f"\n{'='*80}")
        print(f"{method} {endpoint}")
        print(f"Status: {response.status_code}")
        if response.status_code >= 400:
            print(f"ERROR: {response.text[:500]}")
        else:
            print(f"✅ SUCCESS")
            if response.json():
                result = response.json()
                if 'sections' in result:
                    print(f"Sections: {list(result['sections'].keys())}")
                elif 'movies' in result:
                    print(f"Movies returned: {len(result['movies'])}")
        return response.status_code
    except Exception as e:
        print(f"\n{'='*80}")
        print(f"{method} {endpoint}")
        print(f"❌ FAILED: {str(e)}")
        return 0

print("TESTING DASHBOARD APIs...")
print("="*80)

# Test 1: Get personalized sections (THIS IS THE KEY ONE)
test_api("/api/recommendations/sections/zyden04/")

# Test 2: Get continue watching
test_api("/api/analytics/continue-watching/zyden04/")

# Test 3: Get trending
test_api("/api/recommendations/trending/?username=zyden04")

# Test 4: Get movies with filters
test_api("/api/movies/?page=1&limit=12")

print(f"\n{'='*80}")
print("Testing complete!")
