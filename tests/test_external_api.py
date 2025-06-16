import unittest
import requests
from app import create_app

class TestExternalAPI(unittest.TestCase):
    def setUp(self):
        self.app = create_app('testing')
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()

    def tearDown(self):
        self.app_context.pop()

    def test_meal_db_categories(self):
        response = requests.get('https://www.themealdb.com/api/json/v1/1/categories.php')
        self.assertEqual(response.status_code, 200)
        self.assertIn('categories', response.json())

    def test_meal_db_search(self):
        response = requests.get('https://www.themealdb.com/api/json/v1/1/search.php?s=chicken')
        self.assertEqual(response.status_code, 200)
        self.assertIn('meals', response.json())

    def test_meal_db_random(self):
        response = requests.get('https://www.themealdb.com/api/json/v1/1/random.php')
        self.assertEqual(response.status_code, 200)
        self.assertIn('meals', response.json())

if __name__ == '__main__':
    unittest.main() 