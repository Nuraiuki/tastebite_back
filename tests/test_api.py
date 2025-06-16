import unittest
from app import create_app
from app.models import db, User, Recipe

class TestAPI(unittest.TestCase):
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

    def test_home_page(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)

    def test_recipes_endpoint(self):
        response = self.client.get('/api/recipes')
        self.assertEqual(response.status_code, 200)

if __name__ == '__main__':
    unittest.main() 