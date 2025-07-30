#!/usr/bin/env python3

import requests
import json

def check_routes():
    """Check what routes are available on the running server"""
    base_url = "http://172.22.225.49:5100"
    
    # Test the regular endpoint first to make sure server is working
    print("Testing regular endpoint...")
    try:
        response = requests.post(
            base_url + "/api/agent",
            json={"prompt": "test", "patientProfile": {"name": "test"}, "memory": {"id": "memory", "memory": []}},
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        print(f"Regular endpoint status: {response.status_code}")
        if response.status_code == 200:
            print("✅ Regular endpoint is working")
        else:
            print(f"❌ Regular endpoint error: {response.text}")
    except Exception as e:
        print(f"❌ Regular endpoint failed: {e}")
    
    # Test streaming endpoint
    print("\nTesting streaming endpoint...")
    try:
        response = requests.post(
            base_url + "/api/agent/stream",
            json={"prompt": "test", "patientProfile": {"name": "test"}, "memory": {"id": "memory", "memory": []}},
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        print(f"Streaming endpoint status: {response.status_code}")
        if response.status_code == 200:
            print("✅ Streaming endpoint is working")
        else:
            print(f"❌ Streaming endpoint error: {response.text}")
    except Exception as e:
        print(f"❌ Streaming endpoint failed: {e}")
    
    # Test if the route exists by checking different methods
    print("\nTesting different methods on streaming endpoint...")
    methods = ["GET", "POST", "OPTIONS", "PUT", "DELETE"]
    for method in methods:
        try:
            if method == "POST":
                response = requests.post(base_url + "/api/agent/stream", json={}, timeout=5)
            elif method == "OPTIONS":
                response = requests.options(base_url + "/api/agent/stream", timeout=5)
            else:
                response = requests.request(method, base_url + "/api/agent/stream", timeout=5)
            print(f"{method}: {response.status_code}")
        except Exception as e:
            print(f"{method}: Error - {e}")

if __name__ == "__main__":
    check_routes() 