#!/usr/bin/env python3
"""
Quality Check Script for AI-Horizon Ed Platform
Run this before any deployment to catch common issues
"""

import requests
import sys
import json
import time
from datetime import datetime

class QualityChecker:
    def __init__(self, base_url="http://127.0.0.1:9000"):
        self.base_url = base_url
        self.passed_tests = 0
        self.failed_tests = 0
        
    def test_endpoint(self, name, endpoint, expected_status=200, timeout=10):
        """Test a single endpoint"""
        try:
            print(f"Testing {name}... ", end="", flush=True)
            response = requests.get(f"{self.base_url}{endpoint}", timeout=timeout)
            
            if response.status_code == expected_status:
                print("✅ PASSED")
                self.passed_tests += 1
                return True
            else:
                print(f"❌ FAILED (Status: {response.status_code})")
                self.failed_tests += 1
                return False
                
        except requests.exceptions.RequestException as e:
            print(f"❌ ERROR ({str(e)})")
            self.failed_tests += 1
            return False
    
    def test_json_response(self, name, endpoint, required_keys=None, timeout=10):
        """Test endpoint returns valid JSON with required keys"""
        try:
            print(f"Testing {name}... ", end="", flush=True)
            response = requests.get(f"{self.base_url}{endpoint}", timeout=timeout)
            
            if response.status_code != 200:
                print(f"❌ FAILED (Status: {response.status_code})")
                self.failed_tests += 1
                return False
            
            try:
                data = response.json()
                if required_keys:
                    for key in required_keys:
                        if key not in data:
                            print(f"❌ FAILED (Missing key: {key})")
                            self.failed_tests += 1
                            return False
                
                print("✅ PASSED")
                self.passed_tests += 1
                return True
                
            except json.JSONDecodeError:
                print("❌ FAILED (Invalid JSON)")
                self.failed_tests += 1
                return False
                
        except requests.exceptions.RequestException as e:
            print(f"❌ ERROR ({str(e)})")
            self.failed_tests += 1
            return False
    
    def test_quiz_functionality(self):
        """Test quiz grading functionality"""
        print("Testing Quiz Grading... ", end="", flush=True)
        
        try:
            # First get resources to find one with questions
            resources_response = requests.get(f"{self.base_url}/api/resources", timeout=10)
            if resources_response.status_code != 200:
                print("❌ FAILED (Cannot get resources)")
                self.failed_tests += 1
                return False
            
            resources = resources_response.json()
            if not resources.get('resources'):
                print("❌ FAILED (No resources found)")
                self.failed_tests += 1
                return False
            
            # Try to test quiz with first resource
            test_resource_id = resources['resources'][0]['id']
            
            # Test quiz grading with sample answers
            quiz_data = {
                "answers": ["Sample answer for testing", "Another test answer"]
            }
            
            quiz_response = requests.post(
                f"{self.base_url}/api/quiz/{test_resource_id}/grade",
                json=quiz_data,
                timeout=15
            )
            
            if quiz_response.status_code == 200:
                print("✅ PASSED")
                self.passed_tests += 1
                return True
            else:
                print(f"❌ FAILED (Status: {quiz_response.status_code})")
                self.failed_tests += 1
                return False
                
        except Exception as e:
            print(f"❌ ERROR ({str(e)})")
            self.failed_tests += 1
            return False
    
    def run_all_tests(self):
        """Run comprehensive quality checks"""
        print("🔍 AI-Horizon Ed Platform Quality Check")
        print("=" * 50)
        print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        # Core API Tests
        print("📊 Core API Tests:")
        self.test_json_response("Database Stats", "/api/database/stats", 
                              ["total_resources", "by_category"])
        self.test_json_response("Resources API", "/api/resources", 
                              ["resources", "total_count"])
        self.test_json_response("Skills API", "/api/skills/emerging")
        
        # Critical Page Tests
        print("\n🌐 Critical Page Tests:")
        self.test_endpoint("Main Dashboard", "/")
        self.test_endpoint("Skills Overview", "/skills")
        self.test_endpoint("AI-Enhanced SIEM Skill", "/skill/ai-enhanced-siem")
        self.test_endpoint("Vibe Coding Skill", "/skill/vibe-coding")
        self.test_endpoint("Admin Panel", "/admin")
        
        # Database Operations Tests
        print("\n🗃️ Database Operations Tests:")
        self.test_endpoint("Emergency Restore", "/emergency-restore")
        self.test_endpoint("Database Browser", "/database")
        
        # Quiz System Tests
        print("\n🧩 Quiz System Tests:")
        self.test_quiz_functionality()
        
        # Summary
        print("\n" + "=" * 50)
        print(f"✅ Passed: {self.passed_tests}")
        print(f"❌ Failed: {self.failed_tests}")
        print(f"📊 Success Rate: {self.passed_tests/(self.passed_tests+self.failed_tests)*100:.1f}%")
        
        if self.failed_tests == 0:
            print("\n🎉 All tests passed! Platform is ready for deployment.")
            return True
        else:
            print(f"\n🚨 {self.failed_tests} tests failed! Please fix issues before deploying.")
            return False

def main():
    """Main function to run quality checks"""
    print("Starting AI-Horizon Ed Platform Quality Check...")
    print("Make sure the application is running on http://127.0.0.1:9000")
    print()
    
    # Give user time to start the application if needed
    time.sleep(2)
    
    checker = QualityChecker()
    success = checker.run_all_tests()
    
    if success:
        print("\n🚀 Platform is ready for deployment!")
        sys.exit(0)
    else:
        print("\n⚠️  Please fix the issues above before deploying.")
        sys.exit(1)

if __name__ == "__main__":
    main() 