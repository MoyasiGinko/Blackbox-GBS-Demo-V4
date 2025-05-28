#!/usr/bin/env python3
"""
Comprehensive test script for Cookie Management API endpoints
Tests all 18 endpoints covering user, admin, and utility operations
"""

import os
import sys
import django
import requests
import json
from datetime import datetime, timedelta
from django.utils import timezone

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cookie_auth_backend.settings')
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
django.setup()

from django.contrib.auth import get_user_model
from service_app.models import Service
from subscription_app.models import SubscriptionPlan, UserSubscription
from payment_app.models import Payment
from cookie_management_app.models import LoginService, UserService, Cookie

User = get_user_model()

class CookieManagementAPITester:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        self.user_token = None
        self.admin_token = None
        self.test_user = None
        self.test_admin = None
        self.test_service = None
        self.test_subscription_plan = None
        self.login_service_id = None

    def setup_test_data(self):
        """Create test data for the endpoints"""
        print("🔧 Setting up test data...")        # Create test service
        self.test_service, created = Service.objects.get_or_create(
            name="test_seo_tool",
            defaults={
                "display_name": "Test SEO Tool",
                "description": "Test service for cookie management",
                "category": "seo",
                "login_url": "https://test-seo-tool.com/login",
                "is_active": True
            }
        )
        print(f"✓ Service: {self.test_service.name}")        # Create subscription plan
        self.test_subscription_plan, created = SubscriptionPlan.objects.get_or_create(
            name="Test Premium Plan",
            defaults={
                "description": "Test plan for cookie management",
                "price": 29.99,
                "duration_days": 30,
                "max_services": 5,
                "is_active": True
            }
        )
        print(f"✓ Subscription Plan: {self.test_subscription_plan.name}")

        # Create test users
        self.test_user, created = User.objects.get_or_create(
            email="testuser@example.com",
            defaults={
                "full_name": "Test User",
                "is_verified": True
            }        )
        if created:
            self.test_user.set_password("testpass123")
            self.test_user.save()

        self.test_admin, created = User.objects.get_or_create(
            email="admin@example.com",
            defaults={
                "full_name": "Test Admin",
                "is_admin": True,
                "is_verified": True
            }
        )
        # Always set password to ensure it's correct
        self.test_admin.set_password("adminpass123")
        self.test_admin.is_admin = True
        self.test_admin.save()

        print(f"✓ Users: {self.test_user.email}, {self.test_admin.email}")        # Add service to subscription plan
        self.test_subscription_plan.services.add(self.test_service)

        # Create a mock payment for subscription
        payment = Payment.objects.filter(user=self.test_user).first()
        if not payment:
            payment = Payment.objects.create(
                user=self.test_user,
                amount=self.test_subscription_plan.price,
                currency="USD",
                status="completed",
                payment_intent_id=f"test_payment_intent_{self.test_user.id}",
                subscription_plan=self.test_subscription_plan
            )

        # Create user subscription
        user_sub, created = UserSubscription.objects.get_or_create(
            user=self.test_user,
            subscription=self.test_subscription_plan,
            payment=payment,            defaults={
                "is_active": True,
                "expires_at": timezone.now() + timedelta(days=30)
            }
        )
        user_sub.selected_services.add(self.test_service)
        print(f"✓ User Subscription: {user_sub.subscription.name}")

        print("✅ Test data setup complete!\n")

    def authenticate(self):
        """Get authentication tokens for user and admin"""
        print("🔐 Authenticating users...")

        # User authentication
        user_response = requests.post(f"{self.base_url}/api/auth/login/", json={
            "email": "testuser@example.com",
            "password": "testpass123"
        })

        if user_response.status_code == 200:
            self.user_token = user_response.json()["access"]
            print("✓ User authenticated")
        else:
            print(f"❌ User authentication failed: {user_response.text}")
            return False

        # Admin authentication
        admin_response = requests.post(f"{self.base_url}/api/auth/login/", json={
            "email": "admin@example.com",
            "password": "adminpass123"
        })

        if admin_response.status_code == 200:
            self.admin_token = admin_response.json()["access"]
            print("✓ Admin authenticated")
        else:
            print(f"❌ Admin authentication failed: {admin_response.text}")
            return False

        print("✅ Authentication complete!\n")
        return True

    def get_headers(self, is_admin=False):
        """Get headers with authentication token"""
        token = self.admin_token if is_admin else self.user_token
        return {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

    def test_endpoint(self, method, endpoint, data=None, is_admin=False, expected_status=200):
        """Test a single endpoint"""
        url = f"{self.base_url}/api/cookie_management{endpoint}"
        headers = self.get_headers(is_admin)

        try:
            if method == "GET":
                response = requests.get(url, headers=headers)
            elif method == "POST":
                response = requests.post(url, json=data, headers=headers)
            elif method == "PUT":
                response = requests.put(url, json=data, headers=headers)
            elif method == "DELETE":
                response = requests.delete(url, headers=headers)
            else:
                print(f"❌ Unsupported method: {method}")
                return False

            success = response.status_code == expected_status
            status_icon = "✓" if success else "❌"

            print(f"{status_icon} {method} {endpoint} - Status: {response.status_code}")

            if not success:
                print(f"   Expected: {expected_status}, Got: {response.status_code}")
                print(f"   Response: {response.text[:200]}...")

            return success, response

        except Exception as e:
            print(f"❌ {method} {endpoint} - Error: {str(e)}")
            return False, None

    def run_user_endpoint_tests(self):
        """Test all user endpoints"""
        print("👤 Testing USER ENDPOINTS:")
        print("=" * 50)

        # 1. Request Service Access
        success, response = self.test_endpoint(
            "POST", "/request-access/",
            data={"service": str(self.test_service.id)},
            expected_status=201
        )

        # 2. List Accessible Services (initially empty since no approval yet)
        self.test_endpoint("GET", "/my-services/")

        # 3. Try to get cookie (should fail - no access)
        self.test_endpoint(
            "GET", f"/service/{self.test_service.id}/cookie/",
            expected_status=403
        )

        # 4. User Service History
        self.test_endpoint("GET", "/my-history/")

        # 5. User Cookie Activity
        self.test_endpoint("GET", "/my-activity/")

        print("✅ User endpoint tests completed!\n")

    def run_admin_endpoint_tests(self):
        """Test all admin endpoints"""
        print("👨‍💼 Testing ADMIN ENDPOINTS:")
        print("=" * 50)

        # 1. Create Login Service
        success, response = self.test_endpoint(
            "POST", "/admin/login-services/",
            data={
                "service": str(self.test_service.id),
                "username": "test_service_user",
                "password": "test_password",
                "max_concurrent_users": 5,
                "is_active": True
            },
            is_admin=True,
            expected_status=201
        )

        if success and response:
            self.login_service_id = response.json().get("id")
            print(f"   Created login service with ID: {self.login_service_id}")

        # 2. List Login Services
        self.test_endpoint("GET", "/admin/login-services/", is_admin=True)

        # 3. Get Login Service Detail
        if self.login_service_id:
            self.test_endpoint("GET", f"/admin/login-services/{self.login_service_id}/", is_admin=True)

        # 4. List Pending Requests
        self.test_endpoint("GET", "/admin/pending-requests/", is_admin=True)        # Get pending request for approval
        pending_response = requests.get(
            f"{self.base_url}/api/cookie_management/admin/pending-requests/",
            headers=self.get_headers(is_admin=True)
        )

        if pending_response.status_code == 200:
            response_data = pending_response.json()
            # Handle both paginated and non-paginated responses
            if isinstance(response_data, dict) and "results" in response_data:
                pending_requests = response_data["results"]
            else:
                pending_requests = response_data if isinstance(response_data, list) else []

            if pending_requests:
                request_id = pending_requests[0]["id"]

                # 5. Approve Service Request
                self.test_endpoint(
                    "POST", f"/admin/approve-request/{request_id}/",
                    is_admin=True
                )

        # 6. List All User Services
        self.test_endpoint("GET", "/admin/user-services/", is_admin=True)

        # 7. List Cookies
        self.test_endpoint("GET", "/admin/cookies/", is_admin=True)

        # 8. Trigger Cookie Extraction
        if self.login_service_id:
            self.test_endpoint(
                "POST", "/admin/extract-cookies/",
                data={"login_service_id": self.login_service_id},
                is_admin=True,
                expected_status=201
            )

        # 9. List Extraction Jobs
        self.test_endpoint("GET", "/admin/extraction-jobs/", is_admin=True)

        # 10. Cookie Activity Logs
        self.test_endpoint("GET", "/admin/cookie-activity/", is_admin=True)

        # 11. Get Statistics
        self.test_endpoint("GET", "/admin/stats/", is_admin=True)

        print("✅ Admin endpoint tests completed!\n")

    def run_utility_endpoint_tests(self):
        """Test utility endpoints"""
        print("🔧 Testing UTILITY ENDPOINTS:")
        print("=" * 50)

        # 1. Validate Cookies
        self.test_endpoint("POST", "/admin/validate-cookies/", is_admin=True)

        # 2. Cleanup Expired Data
        self.test_endpoint("POST", "/admin/cleanup/", is_admin=True)

        print("✅ Utility endpoint tests completed!\n")

    def run_integration_test(self):
        """Test complete user workflow after admin approval"""
        print("🔄 Testing INTEGRATION WORKFLOW:")
        print("=" * 50)

        # Create a mock cookie for testing
        try:
            # Get approved user service
            user_service = UserService.objects.filter(
                user=self.test_user,
                service=self.test_service,
                status='active'
            ).first()

            if user_service:
                # Create a test cookie
                test_cookie = Cookie.objects.create(
                    user_service=user_service,
                    cookie_data={"test": "cookie_data", "session": "test_session"},
                    session_id="test_session_123",
                    expires_at=timezone.now() + timedelta(hours=24),
                    status='valid'
                )

                print("✓ Created test cookie")

                # Test getting the cookie
                success, response = self.test_endpoint(
                    "GET", f"/service/{self.test_service.id}/cookie/"
                )

                if success:
                    print("✓ Successfully retrieved cookie data")
                    cookie_data = response.json()
                    print(f"   Cookie ID: {cookie_data.get('id')}")
                    print(f"   Service: {cookie_data.get('service_info', {}).get('name')}")

            else:
                print("❌ No active user service found for integration test")

        except Exception as e:
            print(f"❌ Integration test error: {str(e)}")

        print("✅ Integration workflow test completed!\n")

    def run_all_tests(self):
        """Run complete test suite"""
        print("🚀 STARTING COOKIE MANAGEMENT API TESTS")
        print("=" * 60)

        # Setup
        self.setup_test_data()

        if not self.authenticate():
            print("❌ Authentication failed. Stopping tests.")
            return

        # Run test suites
        self.run_user_endpoint_tests()
        self.run_admin_endpoint_tests()
        self.run_utility_endpoint_tests()
        self.run_integration_test()

        print("🎉 ALL TESTS COMPLETED!")
        print("=" * 60)

        # Summary
        print("\n📊 ENDPOINT SUMMARY:")
        print("User Endpoints: 5")
        print("Admin Endpoints: 11")
        print("Utility Endpoints: 2")
        print("Total: 18 endpoints tested")

        print("\n📝 API Documentation available at:")
        print(f"{self.base_url}/swagger/")

if __name__ == "__main__":
    # Start Django development server check
    import subprocess
    import time
    import socket

    def is_server_running(host="localhost", port=8000):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            result = sock.connect_ex((host, port))
            sock.close()
            return result == 0
        except:
            return False

    if not is_server_running():
        print("⚠️  Django development server not running!")
        print("💡 Start server with: python manage.py runserver")
        print("   Then run this test again.")
        sys.exit(1)

    # Run tests
    tester = CookieManagementAPITester()
    tester.run_all_tests()
