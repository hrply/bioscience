import requests
import json

# Base URL for the API
BASE_URL = "http://localhost:20425"

def test_grouping_api():
    """Test the grouping API with various inputs"""
    
    # Test data
    csv_data = """旧编号,体重,摄食量,血糖水平
A1,70.5,200,105
A2,65.2,180,98
A3,72.1,210,110
A4,68.7,190,102
A5,71.3,205,108
A6,66.8,185,100"""
    
    # Test 1: Normal grouping
    print("Test 1: Normal grouping")
    payload = {
        "data": csv_data,
        "group_count": 3,
        "layers": ["体重", "摄食量"]
    }
    
    response = requests.post(f"{BASE_URL}/api/group", json=payload)
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
    print()
    
    # Test 2: Error case - invalid columns
    print("Test 2: Error case - invalid columns")
    payload_error = {
        "data": csv_data,
        "group_count": 3,
        "layers": ["不存在的列"]
    }
    
    response_error = requests.post(f"{BASE_URL}/api/group", json=payload_error)
    print(f"Status: {response_error.status_code}")
    print(f"Response: {json.dumps(response_error.json(), indent=2, ensure_ascii=False)}")
    print()
    
    # Test 3: Error case - empty layers
    print("Test 3: Error case - empty layers")
    payload_empty = {
        "data": csv_data,
        "group_count": 3,
        "layers": []
    }
    
    response_empty = requests.post(f"{BASE_URL}/api/group", json=payload_empty)
    print(f"Status: {response_empty.status_code}")
    print(f"Response: {json.dumps(response_empty.json(), indent=2, ensure_ascii=False)}")
    print()

if __name__ == "__main__":
    test_grouping_api()