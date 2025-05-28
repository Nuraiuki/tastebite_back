"""
Test script to verify admin recipe deletion functionality.
"""

import requests
import json

# Base URL for the API
BASE_URL = 'http://localhost:5001/api'

def test_admin_recipe_delete():
    print("=== TESTING ADMIN RECIPE DELETION ===")
    
    # Step 1: Login as admin
    print("\n1. Logging in as admin...")
    login_response = requests.post(
        f'{BASE_URL}/auth/login',
        json={'email': 'admin@example.com', 'password': 'adminpassword'},  # Replace with actual admin credentials
        headers={'Content-Type': 'application/json'}
    )
    
    if login_response.status_code == 200:
        print("Admin login successful!")
        print(f"Admin data: {login_response.json()}")
        cookies = login_response.cookies
    else:
        print(f"Admin login failed! Status code: {login_response.status_code}")
        print(f"Response: {login_response.text}")
        return
    
    # Step 2: Get list of recipes
    print("\n2. Fetching recipes list...")
    recipes_response = requests.get(
        f'{BASE_URL}/recipes',
        cookies=cookies
    )
    
    if recipes_response.status_code == 200:
        recipes = recipes_response.json()
        print(f"Fetched {len(recipes)} recipes")
        
        if len(recipes) == 0:
            print("No recipes found to delete!")
            return
            
        # Choose a recipe to delete (preferably an external one)
        external_recipes = [r for r in recipes if r.get('is_external')]
        recipe_to_delete = external_recipes[0] if external_recipes else recipes[0]
        
        print(f"Selected recipe to delete: ID {recipe_to_delete['id']} - '{recipe_to_delete['title']}'")
        print(f"Recipe type: {'External' if recipe_to_delete.get('is_external') else 'User-created'}")
        print(f"Owner ID: {recipe_to_delete['user_id']}")
        
        # Step 3: Delete the recipe
        print(f"\n3. Attempting to delete recipe {recipe_to_delete['id']}...")
        delete_response = requests.delete(
            f"{BASE_URL}/recipes/{recipe_to_delete['id']}",
            cookies=cookies
        )
        
        if delete_response.status_code == 200:
            print("Recipe deleted successfully!")
            print(f"Response: {delete_response.json()}")
            
            # Verify deletion
            print("\n4. Verifying deletion...")
            verify_response = requests.get(
                f"{BASE_URL}/recipes/{recipe_to_delete['id']}",
                cookies=cookies
            )
            
            if verify_response.status_code == 404:
                print("Verification successful! Recipe no longer exists.")
            else:
                print(f"Verification failed! Recipe still exists. Status code: {verify_response.status_code}")
        else:
            print(f"Recipe deletion failed! Status code: {delete_response.status_code}")
            print(f"Response: {delete_response.text}")
    else:
        print(f"Failed to fetch recipes! Status code: {recipes_response.status_code}")
        print(f"Response: {recipes_response.text}")

if __name__ == "__main__":
    test_admin_recipe_delete()