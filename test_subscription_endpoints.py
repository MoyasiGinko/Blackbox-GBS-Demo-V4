#!/usr/bin/env python3
"""
Comprehensive test script for subscription API endpoints.
Tests user subscription management, plan browsing, purchasing, and admin functions.
"""

import requests
import json
import sys
from datetime import datetime, timedelta

# Configuration
BASE_URL = "http://localhost:8000/api"
ADMIN_EMAIL = "admin@example.com"
ADMIN_PASSWORD = "admin123"
TEST_USER_EMAIL = "testuser@example.com"
TEST_USER_PASSWORD = "testpass123"

class SubscriptionEndpointTester:
    def __init__(self):
        self.admin_token = None
        self.user_token = None
        self.created_plan_id = None
        self.created_subscription_id = None

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

    def test_subscription_plans_list(self):
        """Test GET /subscription/plans/ - List subscription plans."""
        print("\n📋 Testing subscription plans list...")

        response = requests.get(
            f"{BASE_URL}/subscription/plans/",
            headers=self.get_auth_headers(self.user_token)
        )

        if response.status_code == 200:
            plans = response.json()
            print(f"✅ Plans list successful - Found {len(plans)} plans")
            if plans:
                print(f"   First plan: {plans[0]['name']} - ${plans[0]['price']}")
                self.created_plan_id = plans[0]['id']  # Store for later tests
            return True
        else:
            print(f"❌ Plans list failed: {response.status_code}")
            print(response.text)
            return False

    def test_subscription_plan_detail(self):
        """Test GET /subscription/plans/{id}/ - Get plan details."""
        if not self.created_plan_id:
            print("⏭️  Skipping plan detail test - no plan ID available")
            return True

        print("\n📄 Testing subscription plan detail...")

        response = requests.get(
            f"{BASE_URL}/subscription/plans/{self.created_plan_id}/",
            headers=self.get_auth_headers(self.user_token)
        )

        if response.status_code == 200:
            plan = response.json()
            print(f"✅ Plan detail successful - {plan['name']}")
            print(f"   Services: {plan['service_count']}, Max services: {plan['max_services']}")
            return True
        else:
            print(f"❌ Plan detail failed: {response.status_code}")
            print(response.text)
            return False

    def test_purchase_subscription(self):
        """Test POST /subscription/purchase/ - Purchase a subscription."""
        if not self.created_plan_id:
            print("⏭️  Skipping purchase test - no plan ID available")
            return True

        print("\n💳 Testing subscription purchase...")

        purchase_data = {
            "subscription_plan_id": self.created_plan_id,
            "payment_method": "stripe"
        }

        response = requests.post(
            f"{BASE_URL}/subscription/purchase/",
            json=purchase_data,
            headers=self.get_auth_headers(self.user_token)
        )

        if response.status_code == 201:
            subscription = response.json()
            self.created_subscription_id = subscription['id']
            print(f"✅ Purchase successful - Subscription ID: {subscription['id']}")
            print(f"   Expires: {subscription['expires_at']}")
            return True
        else:
            print(f"❌ Purchase failed: {response.status_code}")
            print(response.text)
            return False

    def test_user_subscriptions_list(self):
        """Test GET /subscription/my-subscriptions/ - List user's subscriptions."""
        print("\n📝 Testing user subscriptions list...")

        response = requests.get(
            f"{BASE_URL}/subscription/my-subscriptions/",
            headers=self.get_auth_headers(self.user_token)
        )

        if response.status_code == 200:
            subscriptions = response.json()
            print(f"✅ User subscriptions list successful - Found {len(subscriptions)} subscriptions")
            if subscriptions:
                sub = subscriptions[0]
                print(f"   Latest: {sub['subscription']['name']} - Active: {sub['is_active']}")
            return True
        else:
            print(f"❌ User subscriptions list failed: {response.status_code}")
            print(response.text)
            return False

    def test_user_active_subscriptions(self):
        """Test GET /subscription/my-subscriptions/active/ - List active subscriptions."""
        print("\n🟢 Testing active subscriptions list...")

        response = requests.get(
            f"{BASE_URL}/subscription/my-subscriptions/active/",
            headers=self.get_auth_headers(self.user_token)
        )

        if response.status_code == 200:
            subscriptions = response.json()
            print(f"✅ Active subscriptions list successful - Found {len(subscriptions)} active")
            return True
        else:
            print(f"❌ Active subscriptions list failed: {response.status_code}")
            print(response.text)
            return False

    def test_subscription_stats(self):
        """Test GET /subscription/my-stats/ - Get user subscription stats."""
        print("\n📊 Testing subscription stats...")

        response = requests.get(
            f"{BASE_URL}/subscription/my-stats/",
            headers=self.get_auth_headers(self.user_token)
        )

        if response.status_code == 200:
            stats = response.json()
            print("✅ Subscription stats successful")
            print(f"   Total subscriptions: {stats['total_subscriptions']}")
            print(f"   Active subscriptions: {stats['active_subscriptions']}")
            print(f"   Total spent: ${stats['total_spent']}")
            return True
        else:
            print(f"❌ Subscription stats failed: {response.status_code}")
            print(response.text)
            return False

    def test_admin_subscription_plans(self):
        """Test GET /subscription/admin/plans/ - Admin subscription plans management."""
        print("\n👑 Testing admin subscription plans...")

        response = requests.get(
            f"{BASE_URL}/subscription/admin/plans/",
            headers=self.get_auth_headers(self.admin_token)
        )

        if response.status_code == 200:
            plans = response.json()
            print(f"✅ Admin plans list successful - Found {len(plans)} plans")
            return True
        else:
            print(f"❌ Admin plans list failed: {response.status_code}")
            print(response.text)
            return False

    def test_admin_create_subscription_plan(self):
        """Test POST /subscription/admin/plans/ - Create new subscription plan."""
        print("\n➕ Testing admin create subscription plan...")

        plan_data = {
            "name": "Test Plan",
            "description": "A test subscription plan created by API test",
            "price": "29.99",
            "duration_days": 30,
            "max_services": 3,
            "is_active": True
        }

        response = requests.post(
            f"{BASE_URL}/subscription/admin/plans/",
            json=plan_data,
            headers=self.get_auth_headers(self.admin_token)
        )

        if response.status_code == 201:
            plan = response.json()
            print(f"✅ Admin plan creation successful - Plan ID: {plan['id']}")
            print(f"   Name: {plan['name']}, Price: ${plan['price']}")
            return True
        else:
            print(f"❌ Admin plan creation failed: {response.status_code}")
            print(response.text)
            return False

    def test_admin_user_subscriptions(self):
        """Test GET /subscription/admin/subscriptions/ - Admin view all subscriptions."""
        print("\n👥 Testing admin user subscriptions list...")

        response = requests.get(
            f"{BASE_URL}/subscription/admin/subscriptions/",
            headers=self.get_auth_headers(self.admin_token)
        )

        if response.status_code == 200:
            subscriptions = response.json()
            print(f"✅ Admin subscriptions list successful - Found {len(subscriptions)} subscriptions")
            if subscriptions:
                sub = subscriptions[0]
                print(f"   Latest: User {sub['user_email']} - Plan {sub['subscription']['name']}")
            return True
        else:
            print(f"❌ Admin subscriptions list failed: {response.status_code}")
            print(response.text)
            return False

    def test_admin_subscription_stats(self):
        """Test GET /subscription/admin/stats/ - Admin subscription statistics."""
        print("\n📈 Testing admin subscription stats...")

        response = requests.get(
            f"{BASE_URL}/subscription/admin/stats/",
            headers=self.get_auth_headers(self.admin_token)
        )

        if response.status_code == 200:
            stats = response.json()
            print("✅ Admin subscription stats successful")
            print(f"   Total plans: {stats['total_plans']}")
            print(f"   Total subscriptions: {stats['total_subscriptions']}")
            print(f"   Active subscriptions: {stats['active_subscriptions']}")
            print(f"   Total revenue: ${stats['total_revenue']}")
            return True
        else:
            print(f"❌ Admin subscription stats failed: {response.status_code}")
            print(response.text)
            return False

    def test_cancel_subscription(self):
        """Test POST /subscription/subscriptions/{id}/cancel/ - Cancel subscription."""
        if not self.created_subscription_id:
            print("⏭️  Skipping cancel test - no subscription ID available")
            return True

        print("\n❌ Testing subscription cancellation...")

        response = requests.post(
            f"{BASE_URL}/subscription/subscriptions/{self.created_subscription_id}/cancel/",
            headers=self.get_auth_headers(self.user_token)
        )

        if response.status_code == 200:
            result = response.json()
            print(f"✅ Subscription cancellation successful")
            print(f"   Message: {result['detail']}")
            return True
        else:
            print(f"❌ Subscription cancellation failed: {response.status_code}")
            print(response.text)
            return False

    def run_all_tests(self):
        """Run all subscription endpoint tests."""
        print("🚀 Starting Subscription API Endpoint Tests")
        print("=" * 60)

        # Login tests
        if not self.login_admin():
            print("❌ Admin login failed - skipping admin tests")
            return False

        if not self.login_user():
            print("❌ User login failed - aborting tests")
            return False

        # User endpoint tests
        user_tests = [
            self.test_subscription_plans_list,
            self.test_subscription_plan_detail,
            self.test_purchase_subscription,
            self.test_user_subscriptions_list,
            self.test_user_active_subscriptions,
            self.test_subscription_stats,
        ]

        # Admin endpoint tests
        admin_tests = [
            self.test_admin_subscription_plans,
            self.test_admin_create_subscription_plan,
            self.test_admin_user_subscriptions,
            self.test_admin_subscription_stats,
        ]

        # Additional tests
        additional_tests = [
            self.test_cancel_subscription,
        ]

        all_tests = user_tests + admin_tests + additional_tests
        passed = 0
        total = len(all_tests)

        for test in all_tests:
            try:
                if test():
                    passed += 1
            except Exception as e:
                print(f"❌ Test {test.__name__} failed with exception: {e}")

        print("\n" + "=" * 60)
        print(f"📊 Test Results: {passed}/{total} tests passed")

        if passed == total:
            print("🎉 All subscription endpoint tests passed!")
            return True
        else:
            print(f"⚠️  {total - passed} tests failed")
            return False

def main():
    """Main function to run tests."""
    tester = SubscriptionEndpointTester()

    try:
        success = tester.run_all_tests()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⏹️  Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
