import requests
import json

BASE_URL = 'http://localhost:5001/api'

def test_health():
    print("\n--- Testing Health Endpoint ---")
    response = requests.get(f'{BASE_URL}/health')
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text}")

def test_registration():
    print("\n--- Testing Registration ---")
    data = {
        "email": "test@example.com",
        "password": "password123",
        "name": "Test User"
    }
    
    response = requests.post(
        f'{BASE_URL}/auth/register',
        json=data,
        headers={'Content-Type': 'application/json'}
    )
    
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text}")
    return response

def test_login():
    print("\n--- Testing Login ---")
    data = {
        "email": "test@example.com",
        "password": "password123"
    }
    
    response = requests.post(
        f'{BASE_URL}/auth/login',
        json=data,
        headers={'Content-Type': 'application/json'}
    )
    
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text}")
    
    return response.cookies if response.ok else None

def test_auth_check(cookies=None):
    print("\n--- Testing Auth Check ---")
    response = requests.get(
        f'{BASE_URL}/auth/check',
        cookies=cookies
    )
    
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text}")

if __name__ == "__main__":
    test_health()
    test_registration()
    cookies = test_login()
    if cookies:
        test_auth_check(cookies) 