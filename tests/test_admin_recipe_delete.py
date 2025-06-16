"""
Test script to verify admin recipe deletion functionality.
"""

import unittest
from app import create_app
from app.models import db, User, Recipe

class TestAdminRecipeDelete(unittest.TestCase):
    def setUp(self):
        self.app = create_app('testing')
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

        # Create admin user
        admin = User(
            name='Admin User',
            email='admin@example.com',
            is_admin=True
        )
        admin.set_password('admin123')
        db.session.add(admin)
        db.session.commit()

        # Create regular user
        user = User(
            name='Regular User',
            email='user@example.com',
            is_admin=False
        )
        user.set_password('user123')
        db.session.add(user)
        db.session.commit()

        # Create test recipe
        recipe = Recipe(
            title='Test Recipe',
            category='Test Category',
            area='Test Area',
            instructions='Test Instructions',
            user_id=user.id
        )
        db.session.add(recipe)
        db.session.commit()

        self.admin_id = admin.id
        self.user_id = user.id
        self.recipe_id = recipe.id

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_admin_delete_recipe(self):
        # Login as admin
        login_response = self.client.post('/api/auth/login', json={
            'email': 'admin@example.com',
            'password': 'admin123'
        })
        self.assertEqual(login_response.status_code, 200)

        # Delete recipe
        response = self.client.delete(f'/api/admin/recipes/{self.recipe_id}')
        self.assertEqual(response.status_code, 200)

        # Verify recipe is deleted
        recipe = Recipe.query.get(self.recipe_id)
        self.assertIsNone(recipe)

    def test_regular_user_cannot_delete_recipe(self):
        # Login as regular user
        login_response = self.client.post('/api/auth/login', json={
            'email': 'user@example.com',
            'password': 'user123'
        })
        self.assertEqual(login_response.status_code, 200)

        # Try to delete recipe
        response = self.client.delete(f'/api/admin/recipes/{self.recipe_id}')
        self.assertEqual(response.status_code, 403)

        # Verify recipe still exists
        recipe = Recipe.query.get(self.recipe_id)
        self.assertIsNotNone(recipe)

if __name__ == '__main__':
    unittest.main()