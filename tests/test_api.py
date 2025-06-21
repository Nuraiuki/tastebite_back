import requests
import json

# Base URL for the API
BASE_URL = 'http://localhost:5001/api'

def test_api():
    # Step 1: Login to get session cookie
    print("=== TESTING LOGIN ===")
    login_response = requests.post(
        f'{BASE_URL}/auth/login',
        json={'email': 'e@gmail.com', 'password': '123456'},
        headers={'Content-Type': 'application/json'}
    )
    
    if login_response.status_code == 200:
        print("Login successful!")
        print(f"User data: {login_response.json()}")
    else:
        print(f"Login failed! Status code: {login_response.status_code}")
        print(f"Response: {login_response.text}")
        return
    
    # Get the session cookie from the login response
    cookies = login_response.cookies
    
    # Step 2: Test auth check endpoint
    print("\n=== TESTING AUTH CHECK ===")
    auth_check_response = requests.get(
        f'{BASE_URL}/auth/check',
        cookies=cookies
    )
    
    if auth_check_response.status_code == 200:
        print("Auth check successful!")
        print(f"User data: {auth_check_response.json()}")
    else:
        print(f"Auth check failed! Status code: {auth_check_response.status_code}")
        print(f"Response: {auth_check_response.text}")
    
    # Get the available recipes
    print("\n=== TESTING RECIPES ENDPOINT ===")
    recipes_response = requests.get(
        f'{BASE_URL}/recipes',
        cookies=cookies
    )
    
    if recipes_response.status_code == 200:
        recipes = recipes_response.json()
        print(f"Found {len(recipes)} recipes:")
        for idx, recipe in enumerate(recipes):
            print(f"{idx+1}. {recipe['title']} (ID: {recipe['id']})")
        
        # Use the first recipe for testing if available
        if recipes:
            recipe_id = recipes[0]['id']
            print(f"\nUsing recipe ID {recipe_id} for testing:")
            
            # Step 3: Test rating functionality
            print("\n=== TESTING RATING ===")
            rating_response = requests.post(
                f'{BASE_URL}/recipes/{recipe_id}/rate',
                json={'value': 5},
                cookies=cookies
            )
            
            if rating_response.status_code == 200:
                print("Rating added successfully!")
                print(f"Response: {rating_response.json()}")
            else:
                print(f"Rating failed! Status code: {rating_response.status_code}")
                print(f"Response: {rating_response.text}")
            
            # Step 4: Test favorite functionality
            print("\n=== TESTING FAVORITE ===")
            favorite_response = requests.post(
                f'{BASE_URL}/recipes/{recipe_id}/favorite',
                cookies=cookies
            )
            
            if favorite_response.status_code == 200:
                print("Favorite toggled successfully!")
                print(f"Response: {favorite_response.json()}")
            else:
                print(f"Favorite failed! Status code: {favorite_response.status_code}")
                print(f"Response: {favorite_response.text}")
            
            # Step 5: Test comments functionality
            print("\n=== TESTING COMMENTS ===")
            comment_response = requests.post(
                f'{BASE_URL}/recipes/{recipe_id}/comments',
                json={'content': 'This is a test comment via API'},
                cookies=cookies
            )
            
            if comment_response.status_code == 201:
                print("Comment added successfully!")
                print(f"Response: {comment_response.json()}")
            else:
                print(f"Comment failed! Status code: {comment_response.status_code}")
                print(f"Response: {comment_response.text}")
            
            # Get all comments for the recipe
            print("\n=== TESTING GET COMMENTS ===")
            get_comments_response = requests.get(
                f'{BASE_URL}/recipes/{recipe_id}/comments',
                cookies=cookies
            )
            
            if get_comments_response.status_code == 200:
                comments = get_comments_response.json()
                print(f"Found {len(comments)} comments:")
                for idx, comment in enumerate(comments):
                    print(f"{idx+1}. {comment['content']} by {comment['user']['name']}")
            else:
                print(f"Get comments failed! Status code: {get_comments_response.status_code}")
                print(f"Response: {get_comments_response.text}")
        else:
            print("No recipes found to test with.")
    else:
        print(f"Failed to get recipes! Status code: {recipes_response.status_code}")
        print(f"Response: {recipes_response.text}")

if __name__ == "__main__":
    test_api() 