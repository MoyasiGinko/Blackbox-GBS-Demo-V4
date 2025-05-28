#!/usr/bin/env python3
"""
Comprehensive test script for all service endpoints in the Group Buy platform.
Tests both user and admin endpoints with proper authentication.
"""

import requests
import json
from datetime import datetime

BASE_URL = "http://127.0.0.1:8000/api"

class ServiceEndpointTester:
    def __init__(self):
        self.access_token = None
        self.admin_token = None
        self.headers = {}
        self.admin_headers = {}

    def authenticate_user(self, username="testuser", password="testpass123"):
        """Authenticate as regular user"""
        login_data = {
            "username": username,
            "password": password
        }

        response = requests.post(f"{BASE_URL}/auth/login/", json=login_data)
        if response.status_code == 200:
            data = response.json()
            self.access_token = data.get('access')
            self.headers = {'Authorization': f'Bearer {self.access_token}'}
            print(f"✅ User authenticated successfully")
            return True
        else:
            print(f"❌ User authentication failed: {response.status_code}")
            print(f"Response: {response.text}")
            return False

    def authenticate_admin(self, username="admin", password="admin123"):
        """Authenticate as admin user"""
        login_data = {
            "username": username,
            "password": password
        }

        response = requests.post(f"{BASE_URL}/auth/login/", json=login_data)
        if response.status_code == 200:
            data = response.json()
            admin_access_token = data.get('access')
            self.admin_headers = {'Authorization': f'Bearer {admin_access_token}'}
            print(f"✅ Admin authenticated successfully")
            return True
        else:
            print(f"❌ Admin authentication failed: {response.status_code}")
            print(f"Response: {response.text}")
            return False

    def test_endpoint(self, method, endpoint, headers=None, data=None, description=""):
        """Test a single endpoint"""
        url = f"{BASE_URL}{endpoint}"
        headers = headers or self.headers

        print(f"\n🔍 Testing: {description}")
        print(f"   {method} {endpoint}")

        try:
            if method.upper() == 'GET':
                response = requests.get(url, headers=headers)
            elif method.upper() == 'POST':
                response = requests.post(url, headers=headers, json=data)
            elif method.upper() == 'PUT':
                response = requests.put(url, headers=headers, json=data)
            elif method.upper() == 'DELETE':
                response = requests.delete(url, headers=headers)
            else:
                print(f"❌ Unsupported method: {method}")
                return False

            if response.status_code in [200, 201, 204]:
                print(f"   ✅ Status: {response.status_code}")
                if response.content:
                    try:
                        json_data = response.json()
                        if isinstance(json_data, list):
                            print(f"   📊 Returned {len(json_data)} items")
                        elif isinstance(json_data, dict):
                            print(f"   📊 Returned data keys: {list(json_data.keys())}")
                    except:
                        print(f"   📄 Response: {response.text[:100]}...")
                return True
            else:
                print(f"   ❌ Status: {response.status_code}")
                print(f"   📄 Response: {response.text}")
                return False

        except requests.exceptions.RequestException as e:
            print(f"   ❌ Request failed: {e}")
            return False

    def run_all_tests(self):
        """Run all service endpoint tests"""
        print("🚀 Starting Service Endpoint Tests")
        print("=" * 50)

        # Test authentication first
        if not self.authenticate_user():
            print("❌ Cannot proceed without user authentication")
            return

        if not self.authenticate_admin():
            print("⚠️  Admin tests will be skipped")

        # Track test results
        results = []

        print("\n" + "=" * 50)
        print("📱 USER ENDPOINTS TESTS")
        print("=" * 50)

        # Test user endpoints
        user_tests = [
            ("GET", "/service/services/", "Browse all available services"),
            ("GET", "/service/categories/", "Get service categories"),
            ("GET", "/service/user/accessible-services/", "Get user's accessible services"),
            ("GET", "/service/user/service-status/", "Get user's service status"),
        ]

        for method, endpoint, description in user_tests:
            result = self.test_endpoint(method, endpoint, self.headers, description=description)
            results.append((description, result))

        # Test admin endpoints if admin is authenticated
        if self.admin_headers:
            print("\n" + "=" * 50)
            print("🔧 ADMIN ENDPOINTS TESTS")
            print("=" * 50)

            admin_tests = [
                ("GET", "/service/admin/services/", "Admin: List all services"),
                ("GET", "/service/admin/user-services/", "Admin: List all user service assignments"),
                ("GET", "/service/admin/stats/", "Admin: Get overall service statistics"),
            ]

            for method, endpoint, description in admin_tests:
                result = self.test_endpoint(method, endpoint, self.admin_headers, description=description)
                results.append((description, result))

        # Print summary
        print("\n" + "=" * 50)
        print("📊 TEST SUMMARY")
        print("=" * 50)

        passed = sum(1 for _, result in results if result)
        total = len(results)

        for description, result in results:
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{status}: {description}")

        print(f"\n🎯 Overall: {passed}/{total} tests passed ({(passed/total)*100:.1f}%)")

        if passed == total:
            print("🎉 All tests passed! Service endpoints are working correctly.")
        else:
            print(f"⚠️  {total - passed} tests failed. Check the output above for details.")

def main():
    tester = ServiceEndpointTester()
    tester.run_all_tests()

if __name__ == "__main__":
    main()
