#!/usr/bin/env python3

import requests
import json
import time
import sys
from typing import Dict, Any, List

class StreamingEndpointTester:
    def __init__(self, base_url: str = "http://localhost:5100"):
        self.base_url = base_url
        self.endpoint = f"{base_url}/api/agent/stream"
        
    def test_basic_connectivity(self) -> bool:
        """Test basic connectivity to the server"""
        print("🔍 Testing basic connectivity...")
        try:
            response = requests.get(f"{self.base_url}/health", timeout=5)
            print(f"✅ Health check status: {response.status_code}")
            return True
        except requests.exceptions.RequestException as e:
            print(f"❌ Health check failed: {e}")
            return False
    
    def test_options_request(self) -> bool:
        """Test OPTIONS request for CORS"""
        print("\n🔍 Testing OPTIONS request...")
        try:
            response = requests.options(self.endpoint, timeout=5)
            print(f"✅ OPTIONS Status: {response.status_code}")
            print(f"✅ CORS Headers: {dict(response.headers)}")
            return response.status_code in [200, 204]
        except Exception as e:
            print(f"❌ OPTIONS request failed: {e}")
            return False
    
    def create_test_data(self, prompt: str, patient_name: str = "Test Patient", age: int = 30) -> Dict[str, Any]:
        """Create standardized test data matching the API's expected format"""
        return {
            "prompt": prompt,
            "patientProfile": {
                "uid": f"test-{int(time.time())}",
                "name": patient_name,
                "age": age,
                "bloodType": "O+",
                "allergies": ["penicillin"],
                "treatment": {
                    "medicationList": ["aspirin", "vitamin D"],
                    "dailyChecklist": ["exercise", "meditation"],
                    "appointment": "2024-01-15 10:00 AM",
                    "recommendations": ["eat more vegetables", "drink 8 glasses of water"],
                    "sleepHours": 8,
                    "sleepQuality": "good"
                }
            },
            "memory": [],
            "updates": [],
            "conversation": {
                "cid": f"conv-{int(time.time())}",
                "tags": [],
                "conversation": []
            }
        }
    
    def test_streaming_response(self, test_name: str, data: Dict[str, Any], expected_keywords: List[str] = None) -> bool:
        """Test a specific streaming request"""
        print(f"\n🔍 Testing: {test_name}")
        print(f"📝 Prompt: '{data['prompt']}'")
        
        try:
            response = requests.post(
                self.endpoint,
                json=data,
                headers={
                    'Content-Type': 'application/json',
                    'Accept': 'text/event-stream'
                },
                timeout=30,
                stream=True
            )
            
            print(f"📊 Response Status: {response.status_code}")
            print(f"📊 Response Headers: {dict(response.headers)}")
            
            if response.status_code != 200:
                print(f"❌ Request failed with status {response.status_code}")
                print(f"❌ Error: {response.text}")
                return False
            
            # Read streaming response
            print("📡 Reading streaming response...")
            chunks = []
            start_time = time.time()
            final_result_received = False
            
            for line in response.iter_lines():
                if line:
                    chunk = line.decode('utf-8')
                    chunks.append(chunk)
                    print(f"📦 Chunk: {chunk}")
                    
                    # Parse JSON chunks to look for final_result
                    try:
                        if chunk.startswith('data: '):
                            json_data = json.loads(chunk[6:])  # Remove 'data: ' prefix
                            if json_data.get('type') == 'final_result':
                                final_result_received = True
                                print("✅ Final result received")
                                break
                    except json.JSONDecodeError:
                        # Not JSON, continue
                        pass
                    
                    # Stop after 15 seconds or if we get a reasonable response
                    if time.time() - start_time > 15 or len(chunks) > 30:
                        break
            
            print(f"✅ Received {len(chunks)} chunks in {time.time() - start_time:.2f}s")
            
            # Validate response
            if not chunks:
                print("❌ No response chunks received")
                return False
            
            # Check for streaming format
            streaming_format_valid = any('data: ' in chunk for chunk in chunks)
            if not streaming_format_valid:
                print("⚠️  Warning: Response doesn't appear to be in Server-Sent Events format")
            
            # Check for expected keywords if provided
            if expected_keywords:
                response_text = " ".join(chunks).lower()
                found_keywords = [kw for kw in expected_keywords if kw.lower() in response_text]
                print(f"🔍 Expected keywords: {expected_keywords}")
                print(f"✅ Found keywords: {found_keywords}")
                if not found_keywords:
                    print("⚠️  Warning: No expected keywords found in response")
            
            # Check for final result
            if final_result_received:
                print("✅ Final result structure received")
                
                # Validate final result structure
                try:
                    for chunk in chunks:
                        if chunk.startswith('data: '):
                            json_data = json.loads(chunk[6:])
                            if json_data.get('type') == 'final_result':
                                data = json_data.get('data', {})
                                required_fields = ['updatedPatientProfile', 'updatedMemory', 'Updates']
                                missing_fields = [field for field in required_fields if field not in data]
                                if missing_fields:
                                    print(f"⚠️  Warning: Final result missing fields: {missing_fields}")
                                else:
                                    print("✅ Final result has all required fields")
                                break
                except Exception as e:
                    print(f"⚠️  Warning: Could not validate final result structure: {e}")
            else:
                print("⚠️  Warning: No final_result chunk received")
            
            return True
            
        except requests.exceptions.Timeout:
            print("❌ Timeout error - server not responding")
            return False
        except requests.exceptions.ConnectionError:
            print("❌ Connection error - server not reachable")
            return False
        except Exception as e:
            print(f"❌ Error: {e}")
            return False
    
    def run_comprehensive_tests(self):
        """Run all comprehensive tests"""
        print("🚀 Starting Comprehensive Streaming Endpoint Tests")
        print("=" * 60)
        
        # Test basic connectivity first
        if not self.test_basic_connectivity():
            print("❌ Basic connectivity failed. Stopping tests.")
            return
        
        # Test OPTIONS request
        if not self.test_options_request():
            print("⚠️  OPTIONS request failed, but continuing with other tests")
        
        # Define test cases
        test_cases = [
            {
                "name": "Simple Greeting",
                "prompt": "Hello, how are you?",
                "expected_keywords": ["hello", "hi", "greeting", "how", "are", "you"]
            },
            {
                "name": "Medical Question",
                "prompt": "I have a headache, what should I do?",
                "expected_keywords": ["headache", "pain", "medical", "doctor", "symptom"]
            },
            {
                "name": "Weather Question",
                "prompt": "What's the weather like today?",
                "expected_keywords": ["weather", "temperature", "forecast", "today"]
            },
            {
                "name": "Technical Question",
                "prompt": "How does machine learning work?",
                "expected_keywords": ["machine", "learning", "ai", "algorithm", "data"]
            },
            {
                "name": "Personal Question",
                "prompt": "What's your name and what can you help me with?",
                "expected_keywords": ["name", "help", "assist", "can", "do"]
            },
            {
                "name": "Longer Request",
                "prompt": "Can you explain the process of photosynthesis in detail?",
                "expected_keywords": ["photosynthesis", "process", "explain", "detail"]
            },
            {
                "name": "Code Request",
                "prompt": "Write a Python function to calculate fibonacci numbers",
                "expected_keywords": ["python", "function", "fibonacci", "calculate", "def"]
            },
            {
                "name": "Empty Prompt",
                "prompt": "",
                "expected_keywords": []
            },
            {
                "name": "Special Characters",
                "prompt": "What does 2+2=? And what about π (pi)?",
                "expected_keywords": ["2+2", "pi", "π", "math", "calculation"]
            },
            {
                "name": "Patient Profile Query",
                "prompt": "What medications am I taking?",
                "expected_keywords": ["aspirin", "vitamin", "medication", "taking"]
            },
            {
                "name": "Patient Profile Update",
                "prompt": "Update my sleep quality to poor",
                "expected_keywords": ["sleep", "quality", "poor", "updated"]
            },
            {
                "name": "Treatment Query",
                "prompt": "What are my daily activities?",
                "expected_keywords": ["exercise", "meditation", "daily", "activities"]
            }
        ]
        
        # Run all test cases
        results = []
        for i, test_case in enumerate(test_cases, 1):
            print(f"\n{'='*20} Test {i}/{len(test_cases)} {'='*20}")
            
            data = self.create_test_data(
                prompt=test_case["prompt"],
                patient_name=f"Patient {i}",
                age=25 + i
            )
            
            success = self.test_streaming_response(
                test_name=test_case["name"],
                data=data,
                expected_keywords=test_case["expected_keywords"]
            )
            
            results.append({
                "test": test_case["name"],
                "success": success,
                "prompt": test_case["prompt"]
            })
        
        # Print summary
        print(f"\n{'='*60}")
        print("📊 TEST SUMMARY")
        print("=" * 60)
        
        successful_tests = [r for r in results if r["success"]]
        failed_tests = [r for r in results if not r["success"]]
        
        print(f"✅ Successful tests: {len(successful_tests)}/{len(results)}")
        print(f"❌ Failed tests: {len(failed_tests)}/{len(results)}")
        
        if successful_tests:
            print("\n✅ Successful tests:")
            for result in successful_tests:
                print(f"  - {result['test']}: '{result['prompt']}'")
        
        if failed_tests:
            print("\n❌ Failed tests:")
            for result in failed_tests:
                print(f"  - {result['test']}: '{result['prompt']}'")
        
        # Overall result
        success_rate = len(successful_tests) / len(results) * 100
        print(f"\n🎯 Overall Success Rate: {success_rate:.1f}%")
        
        if success_rate >= 80:
            print("🎉 Excellent! The streaming endpoint is working well.")
        elif success_rate >= 60:
            print("⚠️  Good performance, but some issues detected.")
        else:
            print("🚨 Significant issues detected. Review the failed tests.")
        
        return success_rate >= 60

def main():
    """Main function to run the tests"""
    # Allow custom base URL
    base_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:5100"
    
    tester = StreamingEndpointTester(base_url)
    success = tester.run_comprehensive_tests()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main() 