#!/usr/bin/env python3
"""
Backend API Testing for Sims 4 Downloader
Tests all API endpoints with simulated download functionality
"""

import requests
import sys
import time
import json
from datetime import datetime

class Sims4DownloaderTester:
    def __init__(self, base_url="https://sims4-downloader.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []
        self.current_download_id = None

    def log_test(self, name, success, details=""):
        """Log test result"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name} - PASSED")
        else:
            print(f"❌ {name} - FAILED: {details}")
        
        self.test_results.append({
            "test": name,
            "success": success,
            "details": details,
            "timestamp": datetime.now().isoformat()
        })

    def test_root_endpoint(self):
        """Test GET /api/ endpoint"""
        try:
            response = requests.get(f"{self.api_url}/", timeout=10)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                expected_message = "The Sims 4 Downloader API"
                if data.get("message") == expected_message:
                    self.log_test("Root API endpoint", True)
                    return True
                else:
                    self.log_test("Root API endpoint", False, f"Wrong message: {data.get('message')}")
                    return False
            else:
                self.log_test("Root API endpoint", False, f"Status code: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Root API endpoint", False, f"Exception: {str(e)}")
            return False

    def test_create_download(self):
        """Test POST /api/downloads"""
        try:
            test_url = "https://drive.google.com/file/d/1ABC123DEF456/view"
            payload = {
                "google_drive_url": test_url,
                "filename": "TheSims4.zip"
            }
            
            response = requests.post(f"{self.api_url}/downloads", json=payload, timeout=10)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                required_fields = ["id", "filename", "total_size", "status", "google_drive_url"]
                
                if all(field in data for field in required_fields):
                    self.current_download_id = data["id"]
                    self.log_test("Create download", True)
                    return True
                else:
                    missing = [f for f in required_fields if f not in data]
                    self.log_test("Create download", False, f"Missing fields: {missing}")
                    return False
            else:
                self.log_test("Create download", False, f"Status code: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Create download", False, f"Exception: {str(e)}")
            return False

    def test_get_download_status(self):
        """Test GET /api/downloads/{id}"""
        if not self.current_download_id:
            self.log_test("Get download status", False, "No download ID available")
            return False
            
        try:
            response = requests.get(f"{self.api_url}/downloads/{self.current_download_id}", timeout=10)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                required_fields = ["id", "filename", "status", "progress", "total_size"]
                
                if all(field in data for field in required_fields):
                    self.log_test("Get download status", True)
                    return True
                else:
                    missing = [f for f in required_fields if f not in data]
                    self.log_test("Get download status", False, f"Missing fields: {missing}")
                    return False
            else:
                self.log_test("Get download status", False, f"Status code: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Get download status", False, f"Exception: {str(e)}")
            return False

    def test_start_download(self):
        """Test POST /api/downloads/{id}/start"""
        if not self.current_download_id:
            self.log_test("Start download", False, "No download ID available")
            return False
            
        try:
            response = requests.post(f"{self.api_url}/downloads/{self.current_download_id}/start", timeout=10)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                if "message" in data and "id" in data:
                    self.log_test("Start download", True)
                    return True
                else:
                    self.log_test("Start download", False, f"Invalid response: {data}")
                    return False
            else:
                self.log_test("Start download", False, f"Status code: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Start download", False, f"Exception: {str(e)}")
            return False

    def test_pause_download(self):
        """Test POST /api/downloads/{id}/pause"""
        if not self.current_download_id:
            self.log_test("Pause download", False, "No download ID available")
            return False
            
        try:
            # Wait a bit for download to start
            time.sleep(1)
            
            response = requests.post(f"{self.api_url}/downloads/{self.current_download_id}/pause", timeout=10)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                if "message" in data and "id" in data:
                    self.log_test("Pause download", True)
                    return True
                else:
                    self.log_test("Pause download", False, f"Invalid response: {data}")
                    return False
            else:
                self.log_test("Pause download", False, f"Status code: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Pause download", False, f"Exception: {str(e)}")
            return False

    def test_resume_download(self):
        """Test POST /api/downloads/{id}/resume"""
        if not self.current_download_id:
            self.log_test("Resume download", False, "No download ID available")
            return False
            
        try:
            response = requests.post(f"{self.api_url}/downloads/{self.current_download_id}/resume", timeout=10)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                if "message" in data and "id" in data:
                    self.log_test("Resume download", True)
                    return True
                else:
                    self.log_test("Resume download", False, f"Invalid response: {data}")
                    return False
            else:
                self.log_test("Resume download", False, f"Status code: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Resume download", False, f"Exception: {str(e)}")
            return False

    def test_download_progress_simulation(self):
        """Test that download progress updates correctly"""
        if not self.current_download_id:
            self.log_test("Download progress simulation", False, "No download ID available")
            return False
            
        try:
            # Start download and wait for progress
            requests.post(f"{self.api_url}/downloads/{self.current_download_id}/start", timeout=10)
            
            # Check progress after a few seconds
            time.sleep(3)
            
            response = requests.get(f"{self.api_url}/downloads/{self.current_download_id}", timeout=10)
            if response.status_code == 200:
                data = response.json()
                progress = data.get("progress", 0)
                status = data.get("status", "")
                
                if progress > 0 and status == "downloading":
                    self.log_test("Download progress simulation", True)
                    return True
                else:
                    self.log_test("Download progress simulation", False, f"Progress: {progress}, Status: {status}")
                    return False
            else:
                self.log_test("Download progress simulation", False, f"Status code: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Download progress simulation", False, f"Exception: {str(e)}")
            return False

    def test_install_endpoint(self):
        """Test POST /api/downloads/{id}/install - should fail if not verified"""
        if not self.current_download_id:
            self.log_test("Install endpoint (before verification)", False, "No download ID available")
            return False
            
        try:
            response = requests.post(f"{self.api_url}/downloads/{self.current_download_id}/install", timeout=10)
            
            # Should fail with 400 if download is not verified
            if response.status_code == 400:
                self.log_test("Install endpoint (before verification)", True, "Correctly rejected unverified download")
                return True
            else:
                self.log_test("Install endpoint (before verification)", False, f"Unexpected status: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Install endpoint (before verification)", False, f"Exception: {str(e)}")
            return False

    def test_list_downloads(self):
        """Test GET /api/downloads"""
        try:
            response = requests.get(f"{self.api_url}/downloads", timeout=10)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                if isinstance(data, list):
                    self.log_test("List downloads", True)
                    return True
                else:
                    self.log_test("List downloads", False, f"Expected list, got: {type(data)}")
                    return False
            else:
                self.log_test("List downloads", False, f"Status code: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("List downloads", False, f"Exception: {str(e)}")
            return False

    def run_all_tests(self):
        """Run all backend tests"""
        print("🚀 Starting Sims 4 Downloader Backend Tests")
        print(f"🔗 Testing API at: {self.api_url}")
        print("=" * 60)
        
        # Test sequence
        tests = [
            self.test_root_endpoint,
            self.test_create_download,
            self.test_get_download_status,
            self.test_list_downloads,
            self.test_start_download,
            self.test_download_progress_simulation,
            self.test_pause_download,
            self.test_resume_download,
            self.test_install_endpoint,
        ]
        
        for test in tests:
            try:
                test()
            except Exception as e:
                print(f"❌ Test {test.__name__} crashed: {str(e)}")
                self.tests_run += 1
            
            # Small delay between tests
            time.sleep(0.5)
        
        # Print summary
        print("\n" + "=" * 60)
        print(f"📊 Test Summary: {self.tests_passed}/{self.tests_run} tests passed")
        print(f"✅ Success Rate: {(self.tests_passed/self.tests_run)*100:.1f}%")
        
        if self.tests_passed == self.tests_run:
            print("🎉 All tests passed!")
            return True
        else:
            print("⚠️  Some tests failed - check details above")
            return False

def main():
    """Main test runner"""
    tester = Sims4DownloaderTester()
    success = tester.run_all_tests()
    
    # Save test results
    with open("/app/test_results_backend.json", "w") as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "total_tests": tester.tests_run,
            "passed_tests": tester.tests_passed,
            "success_rate": (tester.tests_passed/tester.tests_run)*100 if tester.tests_run > 0 else 0,
            "results": tester.test_results
        }, f, indent=2)
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())