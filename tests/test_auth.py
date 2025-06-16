import requests
import json
import unittest
from app import create_app
from app.models import db, User

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

class TestAuth(unittest.TestCase):
    def setUp(self):
        self.app = create_app('testing')
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_register(self):
        response = self.client.post('/api/auth/register', json={
            'name': 'Test User',
            'email': 'test@example.com',
            'password': 'password123'
        })
        self.assertEqual(response.status_code, 201)
        self.assertIn('user', response.json)

    def test_login(self):
        # First create a user
        self.client.post('/api/auth/register', json={
            'name': 'Test User',
            'email': 'test@example.com',
            'password': 'password123'
        })

        # Then try to login
        response = self.client.post('/api/auth/login', json={
            'email': 'test@example.com',
            'password': 'password123'
        })
        self.assertEqual(response.status_code, 200)
        self.assertIn('user', response.json)

    def test_logout(self):
        response = self.client.post('/api/auth/logout')
        self.assertEqual(response.status_code, 200)

if __name__ == "__main__":
    test_health()
    test_registration()
    cookies = test_login()
    if cookies:
        test_auth_check(cookies)
    unittest.main() 