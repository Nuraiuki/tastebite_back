import requests
import json

# Base URL for the API
BASE_URL = 'http://localhost:5001/api'

def test_external_api():
    # Step 1: Login to get session cookie
    print("=== TESTING LOGIN ===")
    login_response = requests.post(
        f'{BASE_URL}/auth/login',
        json={'email': 'e@gmail.com', 'password': '"123456"'},
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
    
    # Step 2: Test importing an external recipe
    print("\n=== TESTING EXTERNAL RECIPE IMPORT ===")
    
    # Use a known MealDB recipe ID
    external_recipe_id = "52772"  # Teriyaki Chicken Casserole from MealDB
    
    # First, get the recipe details from MealDB
    print(f"Fetching recipe details from MealDB for ID: {external_recipe_id}")
    mealdb_response = requests.get(
        f'https://www.themealdb.com/api/json/v1/1/lookup.php?i={external_recipe_id}'
    )
    
    if mealdb_response.status_code == 200 and mealdb_response.json().get('meals'):
        meal_data = mealdb_response.json()['meals'][0]
        print(f"MealDB recipe found: {meal_data['strMeal']}")
        
        # Create the ingredients list
        ingredients = []
        for i in range(1, 21):
            ingredient = meal_data.get(f'strIngredient{i}')
            measure = meal_data.get(f'strMeasure{i}')
            
            if ingredient and ingredient.strip():
                ingredients.append({
                    'name': ingredient,
                    'measure': measure or ''
                })
        
        # Import the recipe
        import_data = {
            'externalId': external_recipe_id,
            'title': meal_data['strMeal'],
            'category': meal_data['strCategory'],
            'area': meal_data['strArea'],
            'instructions': meal_data['strInstructions'],
            'imageUrl': meal_data['strMealThumb'],
            'ingredients': ingredients
        }
        
        import_response = requests.post(
            f'{BASE_URL}/import-external-recipe',
            json=import_data,
            cookies=cookies
        )
        
        if import_response.status_code in [200, 201]:
            print("External recipe imported successfully!")
            recipe_data = import_response.json()
            print(f"Imported recipe ID: {recipe_data['id']}")
            local_recipe_id = recipe_data['id']
            
            # Step 3: Test external interactions
            print("\n=== TESTING EXTERNAL RECIPE INTERACTIONS ===")
            
            # Test Rating
            print("\n-- Testing Rating --")
            rating_response = requests.post(
                f'{BASE_URL}/recipes/{local_recipe_id}/rate',
                json={'value': 5},
                cookies=cookies
            )
            
            if rating_response.status_code == 200:
                print("Rating added successfully!")
                print(f"Response: {rating_response.json()}")
            else:
                print(f"Rating failed! Status code: {rating_response.status_code}")
                print(f"Response: {rating_response.text}")
            
            # Test Favorite
            print("\n-- Testing Favorite --")
            favorite_response = requests.post(
                f'{BASE_URL}/recipes/{local_recipe_id}/favorite',
                cookies=cookies
            )
            
            if favorite_response.status_code == 200:
                print("Favorite toggled successfully!")
                print(f"Response: {favorite_response.json()}")
            else:
                print(f"Favorite failed! Status code: {favorite_response.status_code}")
                print(f"Response: {favorite_response.text}")
            
            # Test Comments
            print("\n-- Testing Comments --")
            comment_response = requests.post(
                f'{BASE_URL}/recipes/{local_recipe_id}/comments',
                json={'content': 'This is a test comment on an external recipe'},
                cookies=cookies
            )
            
            if comment_response.status_code == 201:
                print("Comment added successfully!")
                print(f"Response: {comment_response.json()}")
            else:
                print(f"Comment failed! Status code: {comment_response.status_code}")
                print(f"Response: {comment_response.text}")
            
            # Get Comments
            print("\n-- Testing Get Comments --")
            get_comments_response = requests.get(
                f'{BASE_URL}/recipes/{local_recipe_id}/comments',
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
            
            # Test Get Profile to verify favorites and ratings appear
            print("\n=== TESTING PROFILE DATA ===")
            profile_response = requests.get(
                f'{BASE_URL}/user/profile',
                cookies=cookies
            )
            
            if profile_response.status_code == 200:
                profile_data = profile_response.json()
                
                print(f"User: {profile_data['name']}")
                print(f"Total recipes: {len(profile_data['recipes'])}")
                print(f"Total favorites: {len(profile_data['favorites'])}")
                print(f"Total rated recipes: {len(profile_data['rated_recipes'])}")
                
                # Check if our external recipe is in favorites
                external_in_favorites = any(fav.get('id') == local_recipe_id for fav in profile_data['favorites'])
                print(f"External recipe in favorites: {external_in_favorites}")
                
                # Check if our external recipe is in rated recipes
                external_in_rated = any(rated.get('id') == local_recipe_id for rated in profile_data['rated_recipes'])
                print(f"External recipe in rated recipes: {external_in_rated}")
            else:
                print(f"Get profile failed! Status code: {profile_response.status_code}")
                print(f"Response: {profile_response.text}")
        else:
            print(f"Import failed! Status code: {import_response.status_code}")
            print(f"Response: {import_response.text}")
    else:
        print(f"Failed to get recipe from MealDB! Status code: {mealdb_response.status_code}")
        print(f"Response: {mealdb_response.text}")

if __name__ == "__main__":
    test_external_api() 