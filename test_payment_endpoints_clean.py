#!/usr/bin/env python3
"""
Comprehensive test script for payment API endpoints.
Tests payment creation, processing, history, refunds, and admin functions.
"""

import requests
import json
import sys
import time
from datetime import datetime, timedelta

# Configuration
BASE_URL = "http://localhost:8000/api"
ADMIN_EMAIL = "admin@example.com"
ADMIN_PASSWORD = "admin123"
TEST_USER_EMAIL = "testuser@example.com"
TEST_USER_PASSWORD = "testpass123"

class PaymentEndpointTester:
    def __init__(self):
        self.admin_token = None
        self.user_token = None
        self.created_payment_id = None
        self.subscription_plan_id = None

    def get_auth_headers(self, token):
        """Get authorization headers for API requests."""
        return {"Authorization": f"Bearer {token}"}

    def login_admin(self):
        """Login as admin user."""
        print("🔐 Logging in as admin...")
        response = requests.post(f"{BASE_URL}/auth/login/", {
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })

        if response.status_code == 200:
            self.admin_token = response.json()["access"]
            print("✅ Admin login successful")
            return True
        else:
            print(f"❌ Admin login failed: {response.status_code}")
            print(response.text)
            return False

    def login_user(self):
        """Login as regular user."""
        print("🔐 Logging in as test user...")
        response = requests.post(f"{BASE_URL}/auth/login/", {
            "email": TEST_USER_EMAIL,
            "password": TEST_USER_PASSWORD
        })

        if response.status_code == 200:
            self.user_token = response.json()["access"]
            print("✅ User login successful")
            return True
        else:
            print(f"❌ User login failed: {response.status_code}")
            print(response.text)
            return False

    def get_subscription_plan(self):
        """Get a subscription plan for testing."""
        print("📋 Getting subscription plan for testing...")
        response = requests.get(
            f"{BASE_URL}/subscription/plans/",
            headers=self.get_auth_headers(self.user_token)
        )

        if response.status_code == 200:
            plans = response.json()
            if plans:
                plan = plans[0]
                self.subscription_plan_id = plan['id']
                print(f"✅ Got subscription plan: {plan['name']}")
                return True

        print("❌ Could not get subscription plan")
        return False

    def test_create_payment(self):
        """Test POST /payment/create/ - Create a new payment."""
        if not self.subscription_plan_id:
            print("⏭️  Skipping payment creation test - no subscription plan available")
            return True

        print("\n💳 Testing payment creation...")

        payment_data = {
            "subscription_plan_id": self.subscription_plan_id,
            "payment_method": "stripe"
        }

        response = requests.post(
            f"{BASE_URL}/payment/create/",
            json=payment_data,
            headers=self.get_auth_headers(self.user_token)
        )

        if response.status_code == 201:
            payment = response.json()
            self.created_payment_id = payment['id']
            print(f"✅ Payment creation successful - Payment ID: {payment['id']}")
            print(f"   Amount: ${payment['amount']}, Status: {payment['payment_status']}")
            return True
        else:
            print(f"❌ Payment creation failed: {response.status_code}")
            print(response.text)
            return False

    def test_process_payment(self):
        """Test POST /payment/process/ - Process payment confirmation."""
        if not self.created_payment_id:
            print("⏭️  Skipping payment processing test - no payment ID available")
            return True

        print("\n⚡ Testing payment processing...")

        process_data = {
            "payment_id": self.created_payment_id,
            "external_transaction_id": f"stripe_test_{int(time.time() * 1000)}",
            "payment_status": "success",
            "gateway_response": {
                "gateway": "stripe",
                "transaction_fee": 0.30,
                "currency": "USD"
            }
        }

        response = requests.post(
            f"{BASE_URL}/payment/process/",
            json=process_data,
            headers=self.get_auth_headers(self.user_token)
        )

        if response.status_code == 200:
            result = response.json()
            print(f"✅ Payment processing successful")
            print(f"   Message: {result['message']}")
            print(f"   Updated Status: {result['payment']['payment_status']}")
            return True
        else:
            print(f"❌ Payment processing failed: {response.status_code}")
            print(response.text)
            return False

    def test_user_payment_history(self):
        """Test GET /payment/my-payments/ - Get user payment history."""
        print("\n📋 Testing user payment history...")

        response = requests.get(
            f"{BASE_URL}/payment/my-payments/",
            headers=self.get_auth_headers(self.user_token)
        )

        if response.status_code == 200:
            payments = response.json()
            print(f"✅ Payment history successful - Found {len(payments)} payments")
            if payments:
                payment = payments[0]
                print(f"   Latest: ${payment['amount']} - {payment['payment_status']}")
            return True
        else:
            print(f"❌ Payment history failed: {response.status_code}")
            print(response.text)
            return False

    def test_user_payment_detail(self):
        """Test GET /payment/my-payments/{id}/ - Get payment details."""
        if not self.created_payment_id:
            print("⏭️  Skipping payment detail test - no payment ID available")
            return True

        print("\n📄 Testing user payment detail...")

        response = requests.get(
            f"{BASE_URL}/payment/my-payments/{self.created_payment_id}/",
            headers=self.get_auth_headers(self.user_token)
        )

        if response.status_code == 200:
            payment = response.json()
            print(f"✅ Payment detail successful")
            print(f"   Payment ID: {payment['id']}")
            print(f"   User: {payment['user']['email']}")
            print(f"   Plan: {payment['subscription_plan']['name']}")
            return True
        else:
            print(f"❌ Payment detail failed: {response.status_code}")
            print(response.text)
            return False

    def test_user_payment_stats(self):
        """Test GET /payment/my-stats/ - Get user payment statistics."""
        print("\n📊 Testing user payment stats...")

        response = requests.get(
            f"{BASE_URL}/payment/my-stats/",
            headers=self.get_auth_headers(self.user_token)
        )

        if response.status_code == 200:
            stats = response.json()
            print("✅ Payment stats successful")
            print(f"   Total payments: {stats['total_payments']}")
            print(f"   Successful payments: {stats['successful_payments']}")
            print(f"   Total spent: ${stats['total_spent']}")
            return True
        else:
            print(f"❌ Payment stats failed: {response.status_code}")
            print(response.text)
            return False

    def test_admin_payment_list(self):
        """Test GET /payment/admin/payments/ - Admin payment list."""
        print("\n👑 Testing admin payment list...")

        response = requests.get(
            f"{BASE_URL}/payment/admin/payments/",
            headers=self.get_auth_headers(self.admin_token)
        )

        if response.status_code == 200:
            payments = response.json()
            print(f"✅ Admin payment list successful - Found {len(payments)} payments")
            if payments:
                payment = payments[0]
                print(f"   Latest: {payment['user_email']} - ${payment['amount']}")
            return True
        else:
            print(f"❌ Admin payment list failed: {response.status_code}")
            print(response.text)
            return False

    def test_admin_payment_detail(self):
        """Test GET /payment/admin/payments/{id}/ - Admin payment detail."""
        if not self.created_payment_id:
            print("⏭️  Skipping admin payment detail test - no payment ID available")
            return True

        print("\n🔍 Testing admin payment detail...")

        response = requests.get(
            f"{BASE_URL}/payment/admin/payments/{self.created_payment_id}/",
            headers=self.get_auth_headers(self.admin_token)
        )

        if response.status_code == 200:
            payment = response.json()
            print(f"✅ Admin payment detail successful")
            print(f"   Payment ID: {payment['id']}")
            print(f"   User: {payment['user']['email']}")
            print(f"   Status: {payment['payment_status']}")
            return True
        else:
            print(f"❌ Admin payment detail failed: {response.status_code}")
            print(response.text)
            return False

    def test_admin_payment_stats(self):
        """Test GET /payment/admin/stats/ - Admin payment statistics."""
        print("\n📈 Testing admin payment stats...")

        response = requests.get(
            f"{BASE_URL}/payment/admin/stats/",
            headers=self.get_auth_headers(self.admin_token)
        )

        if response.status_code == 200:
            stats = response.json()
            print("✅ Admin payment stats successful")
            print(f"   Total payments: {stats['total_payments']}")
            print(f"   Success rate: {stats['success_rate']}%")
            print(f"   Total revenue: ${stats['total_revenue']}")
            return True
        else:
            print(f"❌ Admin payment stats failed: {response.status_code}")
            print(response.text)
            return False

    def test_admin_refund_payment(self):
        """Test POST /payment/admin/refund/ - Admin refund payment."""
        if not self.created_payment_id:
            print("⏭️  Skipping refund test - no payment ID available")
            return True

        print("\n💸 Testing admin payment refund...")

        refund_data = {
            "payment_id": self.created_payment_id,
            "refund_reason": "API test refund"
        }

        response = requests.post(
            f"{BASE_URL}/payment/admin/refund/",
            json=refund_data,
            headers=self.get_auth_headers(self.admin_token)
        )

        if response.status_code == 200:
            result = response.json()
            print(f"✅ Payment refund successful")
            print(f"   Message: {result['message']}")
            print(f"   Updated Status: {result['payment']['payment_status']}")
            return True
        else:
            print(f"❌ Payment refund failed: {response.status_code}")
            print(response.text)
            return False

    def run_all_tests(self):
        """Run all payment endpoint tests."""
        print("🚀 Starting Payment API Endpoint Tests")
        print("=" * 60)

        # Login tests
        if not self.login_admin():
            print("❌ Admin login failed - skipping admin tests")
            return False

        if not self.login_user():
            print("❌ User login failed - aborting tests")
            return False

        # Get subscription plan for testing
        if not self.get_subscription_plan():
            print("❌ Could not get subscription plan - aborting tests")
            return False

        # User endpoint tests
        user_tests = [
            self.test_create_payment,
            self.test_process_payment,
            self.test_user_payment_history,
            self.test_user_payment_detail,
            self.test_user_payment_stats,
        ]

        # Admin endpoint tests
        admin_tests = [
            self.test_admin_payment_list,
            self.test_admin_payment_detail,
            self.test_admin_payment_stats,
            self.test_admin_refund_payment,
        ]

        all_tests = user_tests + admin_tests
        passed = 0
        total = len(all_tests)

        for test in all_tests:
            try:
                if test():
                    passed += 1
            except Exception as e:
                print(f"❌ Test {test.__name__} failed with exception: {str(e)}")

        print("=" * 60)
        print(f"📊 Test Results: {passed}/{total} tests passed")
        if passed < total:
            print(f"⚠️  {total - passed} tests failed")
            return False
        else:
            print("🎉 All tests passed!")
            return True

def main():
    """Main function to run the payment endpoint tests."""
    print("🚀 Starting Payment API Endpoint Tests")
    tester = PaymentEndpointTester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
