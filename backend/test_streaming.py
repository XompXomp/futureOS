#!/usr/bin/env python3

import requests
import json

def test_streaming_endpoint():
    """Test the streaming endpoint"""
    url = "http://172.22.225.49:5100/api/agent/stream"
    
    # Test data
    data = {
        "prompt": "hello",
        "patientProfile": {
            "name": "test",
            "age": 30,
            "uid": "test-001"
        },
        "memory": {
            "id": "memory",
            "memory": []
        }
    }
    
    try:
        print(f"Testing streaming endpoint: {url}")
        print(f"Data: {json.dumps(data, indent=2)}")
        
        # Test OPTIONS request first
        print("\n1. Testing OPTIONS request...")
        response = requests.options(url, timeout=5)
        print(f"OPTIONS Status: {response.status_code}")
        print(f"OPTIONS Headers: {dict(response.headers)}")
        
        # Test POST request
        print("\n2. Testing POST request...")
        response = requests.post(
            url,
            json=data,
            headers={
                'Content-Type': 'application/json',
                'Accept': 'text/event-stream'
            },
            timeout=10,
            stream=True
        )
        
        print(f"POST Status: {response.status_code}")
        print(f"POST Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            print("\n3. Reading streaming response...")
            for line in response.iter_lines():
                if line:
                    print(f"Received: {line.decode()}")
                    break  # Just read first line for testing
        else:
            print(f"Error: {response.text}")
            
    except requests.exceptions.Timeout:
        print("Timeout error - server not responding")
    except requests.exceptions.ConnectionError:
        print("Connection error - server not reachable")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_streaming_endpoint() 