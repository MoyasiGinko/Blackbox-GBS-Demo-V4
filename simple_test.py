#!/usr/bin/env python3
"""
Simple logout test
"""
import requests
import json

# Get fresh tokens
login_response = requests.post(
    "http://127.0.0.1:8000/api/auth/login/",
    json={"email": "test2@example.com", "password": "testpassword123"}
)

if login_response.status_code == 200:
    tokens = login_response.json()
    access_token = tokens['access']
    refresh_token = tokens['refresh']

    print("✓ Login successful")
    print(f"Access token: {access_token[:50]}...")
    print(f"Refresh token: {refresh_token[:50]}...")

    # Test logout
    logout_response = requests.post(
        "http://127.0.0.1:8000/api/auth/logout/",
        headers={"Authorization": f"Bearer {access_token}"},
        json={"refresh_token": refresh_token}
    )

    print(f"\nLogout status: {logout_response.status_code}")
    print(f"Logout response: {logout_response.text}")

    if logout_response.status_code == 200:
        print("✓ Logout successful!")

        # Try to refresh the token (should fail)
        refresh_response = requests.post(
            "http://127.0.0.1:8000/api/auth/refresh/",
            json={"refresh": refresh_token}
        )

        print(f"\nRefresh attempt status: {refresh_response.status_code}")
        print(f"Refresh attempt response: {refresh_response.text}")

        if refresh_response.status_code == 401:
            print("✓ Token successfully blacklisted!")
        else:
            print("✗ Token was not blacklisted")
    else:
        print("✗ Logout failed")
else:
    print(f"Login failed: {login_response.text}")
