#!/usr/bin/env python3
"""
Test script for the logout endpoint
"""
import requests
import json

BASE_URL = "http://127.0.0.1:8000"

def test_logout_endpoint():
    print("Testing logout endpoint...")

    # First, let's register a test user
    register_data = {
        "email": "test@example.com",
        "full_name": "Test User",
        "password": "testpassword123"
    }

    print("1. Registering test user...")
    response = requests.post(f"{BASE_URL}/api/register/", json=register_data)
    print(f"Register response: {response.status_code}")
    if response.status_code != 201:
        print(f"Register failed: {response.text}")
        return

    # Now let's login to get tokens
    login_data = {
        "email": "test@example.com",
        "password": "testpassword123"
    }

    print("2. Logging in to get tokens...")
    response = requests.post(f"{BASE_URL}/api/auth/login/", json=login_data)
    print(f"Login response: {response.status_code}")
    if response.status_code != 200:
        print(f"Login failed: {response.text}")
        return

    tokens = response.json()
    access_token = tokens.get('access')
    refresh_token = tokens.get('refresh')

    print(f"Access token received: {access_token[:50]}..." if access_token else "No access token")
    print(f"Refresh token received: {refresh_token[:50]}..." if refresh_token else "No refresh token")

    # Test the profile endpoint to ensure authentication works
    headers = {"Authorization": f"Bearer {access_token}"}
    print("3. Testing profile endpoint with token...")
    response = requests.get(f"{BASE_URL}/api/profile/", headers=headers)
    print(f"Profile response: {response.status_code}")
    if response.status_code == 200:
        print("✓ Authentication is working!")
    else:
        print(f"✗ Authentication failed: {response.text}")
        return

    # Now test the logout endpoint
    logout_data = {"refresh_token": refresh_token}
    print("4. Testing logout endpoint...")
    response = requests.post(f"{BASE_URL}/api/auth/logout/", json=logout_data, headers=headers)
    print(f"Logout response: {response.status_code}")
    print(f"Logout response body: {response.text}")

    if response.status_code == 200:
        print("✓ Logout successful!")

        # Try to use the refresh token again (should fail)
        print("5. Testing if refresh token is blacklisted...")
        refresh_data = {"refresh": refresh_token}
        response = requests.post(f"{BASE_URL}/api/auth/refresh/", json=refresh_data)
        print(f"Refresh attempt response: {response.status_code}")
        if response.status_code == 401:
            print("✓ Refresh token successfully blacklisted!")
        else:
            print(f"✗ Refresh token not blacklisted: {response.text}")
    else:
        print(f"✗ Logout failed: {response.text}")

if __name__ == "__main__":
    test_logout_endpoint()
