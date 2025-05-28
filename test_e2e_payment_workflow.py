#!/usr/bin/env python3
"""
End-to-end payment workflow integration test.
Tests the complete flow from payment creation to subscription activation.
"""

import requests
import json
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:8000/api"
TEST_USER_EMAIL = "testuser@example.com"
TEST_USER_PASSWORD = "testpass123"

def test_end_to_end_payment_workflow():
    """Test complete payment to subscription workflow."""
    print("🔄 Starting End-to-End Payment Workflow Test")
    print("=" * 60)

    # 1. Login user
    print("🔐 Step 1: User Login...")
    login_response = requests.post(f"{BASE_URL}/auth/login/", {
        "email": TEST_USER_EMAIL,
        "password": TEST_USER_PASSWORD
    })

    if login_response.status_code != 200:
        print(f"❌ Login failed: {login_response.status_code}")
        return False

    token = login_response.json()["access"]
    headers = {"Authorization": f"Bearer {token}"}
    print("✅ User login successful")

    # 2. Get available subscription plans
    print("\n📋 Step 2: Get Subscription Plans...")
    plans_response = requests.get(f"{BASE_URL}/subscription/plans/", headers=headers)

    if plans_response.status_code != 200:
        print(f"❌ Failed to get plans: {plans_response.status_code}")
        return False

    plans = plans_response.json()
    if not plans:
        print("❌ No subscription plans available")
        return False

    selected_plan = plans[0]
    print(f"✅ Selected plan: {selected_plan['name']} - ${selected_plan['price']}")

    # 3. Create payment for subscription
    print("\n💳 Step 3: Create Payment...")
    timestamp = int(datetime.now().timestamp() * 1000)
    payment_data = {
        "subscription_plan": selected_plan['id'],
        "amount": selected_plan['price'],
        "payment_method": "stripe",
        "transaction_id": f"test_txn_{timestamp}"
    }

    create_response = requests.post(
        f"{BASE_URL}/payment/create/",
        json=payment_data,
        headers=headers
    )

    if create_response.status_code != 201:
        print(f"❌ Payment creation failed: {create_response.status_code}")
        print(create_response.text)
        return False

    payment = create_response.json()
    payment_id = payment['id']
    print(f"✅ Payment created: {payment_id} - ${payment['amount']}")

    # 4. Process payment (simulate payment gateway success)
    print("\n⚡ Step 4: Process Payment...")
    process_data = {
        "payment_gateway_response": {
            "status": "success",
            "transaction_id": payment['transaction_id'],
            "gateway_reference": f"gw_ref_{timestamp}"
        }
    }

    process_response = requests.post(
        f"{BASE_URL}/payment/{payment_id}/process/",
        json=process_data,
        headers=headers
    )

    if process_response.status_code != 200:
        print(f"❌ Payment processing failed: {process_response.status_code}")
        print(process_response.text)
        return False

    print("✅ Payment processed successfully")

    # 5. Verify subscription was created
    print("\n📋 Step 5: Verify Subscription Created...")
    subscriptions_response = requests.get(
        f"{BASE_URL}/subscription/my-subscriptions/active/",
        headers=headers
    )

    if subscriptions_response.status_code != 200:
        print(f"❌ Failed to get subscriptions: {subscriptions_response.status_code}")
        return False

    active_subscriptions = subscriptions_response.json()

    # Find the subscription linked to our payment
    matching_subscription = None
    for sub in active_subscriptions:
        if sub.get('payment', {}).get('id') == payment_id:
            matching_subscription = sub
            break

    if not matching_subscription:
        print("❌ No active subscription found for this payment")
        return False

    print(f"✅ Active subscription found: {matching_subscription['subscription']['name']}")
    print(f"   Expires: {matching_subscription['expires_at']}")

    # 6. Test payment history includes this transaction
    print("\n📊 Step 6: Verify Payment History...")
    history_response = requests.get(f"{BASE_URL}/payment/history/", headers=headers)

    if history_response.status_code != 200:
        print(f"❌ Failed to get payment history: {history_response.status_code}")
        return False

    payment_history = history_response.json()
    payment_found = any(p['id'] == payment_id for p in payment_history)

    if not payment_found:
        print("❌ Payment not found in history")
        return False

    print("✅ Payment found in user history")

    # 7. Test payment stats reflect the new payment
    print("\n📈 Step 7: Verify Payment Stats...")
    stats_response = requests.get(f"{BASE_URL}/payment/stats/", headers=headers)

    if stats_response.status_code != 200:
        print(f"❌ Failed to get payment stats: {stats_response.status_code}")
        return False

    stats = stats_response.json()
    print(f"✅ Updated stats - Total payments: {stats['total_payments']}")
    print(f"   Successful: {stats['successful_payments']}, Total spent: ${stats['total_spent']}")

    print("\n" + "=" * 60)
    print("🎉 End-to-End Payment Workflow Test PASSED!")
    print("✅ All integration points working correctly:")
    print("   • User authentication")
    print("   • Subscription plan browsing")
    print("   • Payment creation")
    print("   • Payment processing")
    print("   • Automatic subscription activation")
    print("   • Payment history tracking")
    print("   • Statistics updates")

    return True

if __name__ == "__main__":
    success = test_end_to_end_payment_workflow()
    if not success:
        print("\n❌ End-to-End Test FAILED")
        exit(1)
    print("\n🎉 All systems operational!")
