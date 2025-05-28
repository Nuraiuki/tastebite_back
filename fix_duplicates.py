"""
Script to fix duplicate external recipes in the database.
This script:
1. Finds all external recipes with the same external_id
2. Keeps one copy (preferably the one owned by the system user)
3. Updates all interactions (favorites, ratings, comments) to point to the kept recipe
4. Deletes the duplicate recipes
"""

import os
import sys

# Add the app directory to the path so we can import the models
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import Flask app and database models
from app import create_app, db
from app.models import Recipe, User, Favorite, Rating, Comment

app = create_app()

def fix_duplicate_recipes():
    with app.app_context():
        print("Fixing duplicate external recipes...")
        # Get all distinct external_id values that have more than one recipe
        external_ids_query = db.session.query(Recipe.external_id, db.func.count(Recipe.id).label('count')) \
            .filter(Recipe.is_external == True, Recipe.external_id != None) \
            .group_by(Recipe.external_id) \
            .having(db.func.count(Recipe.id) > 1)
        
        duplicates = external_ids_query.all()
        print(f"Found {len(duplicates)} external recipes with duplicates")
        
        # Get the system user
        system_user = User.query.filter_by(email="system@tastebite.com").first()
        if not system_user:
            print("Creating system user...")
            system_user = User(
                name="Tastebite System",
                email="system@tastebite.com",
                pw_hash="",
                is_system=True
            )
            db.session.add(system_user)
            db.session.commit()
            print(f"Created system user with ID {system_user.id}")
        
        # Process each external_id with duplicates
        for external_id, count in duplicates:
            print(f"\nProcessing external_id: {external_id} with {count} duplicates")
            
            # Get all recipes with this external_id
            recipes = Recipe.query.filter_by(external_id=external_id, is_external=True).all()
            
            # Try to find the recipe owned by the system user first
            system_recipe = next((r for r in recipes if r.user_id == system_user.id), None)
            
            # If no system recipe, use the first one
            recipe_to_keep = system_recipe or recipes[0]
            print(f"Keeping recipe ID {recipe_to_keep.id} ('{recipe_to_keep.title}')")
            
            # Assign it to the system user if it's not already
            if recipe_to_keep.user_id != system_user.id:
                recipe_to_keep.user_id = system_user.id
                print(f"Reassigning recipe {recipe_to_keep.id} to system user")
                
            # Get recipes to delete
            recipes_to_delete = [r for r in recipes if r.id != recipe_to_keep.id]
            
            # Process each recipe to delete
            for recipe in recipes_to_delete:
                print(f"Processing recipe {recipe.id} to delete")
                
                # Update favorites to point to the recipe we're keeping
                favorites = Favorite.query.filter_by(recipe_id=recipe.id).all()
                for fav in favorites:
                    # Check if user already has this recipe as favorite
                    existing_fav = Favorite.query.filter_by(
                        user_id=fav.user_id, 
                        recipe_id=recipe_to_keep.id
                    ).first()
                    
                    if existing_fav:
                        print(f"User {fav.user_id} already has recipe {recipe_to_keep.id} as favorite, deleting duplicate")
                        db.session.delete(fav)
                    else:
                        print(f"Updating favorite from user {fav.user_id} to point to recipe {recipe_to_keep.id}")
                        fav.recipe_id = recipe_to_keep.id
                
                # Update ratings to point to the recipe we're keeping
                ratings = Rating.query.filter_by(recipe_id=recipe.id).all()
                for rating in ratings:
                    # Check if user already rated the recipe we're keeping
                    existing_rating = Rating.query.filter_by(
                        user_id=rating.user_id, 
                        recipe_id=recipe_to_keep.id
                    ).first()
                    
                    if existing_rating:
                        print(f"User {rating.user_id} already rated recipe {recipe_to_keep.id}, keeping most recent")
                        # Keep the most recent rating
                        if rating.created_at > existing_rating.created_at:
                            existing_rating.value = rating.value
                            existing_rating.created_at = rating.created_at
                        db.session.delete(rating)
                    else:
                        print(f"Updating rating from user {rating.user_id} to point to recipe {recipe_to_keep.id}")
                        rating.recipe_id = recipe_to_keep.id
                
                # Update comments to point to the recipe we're keeping
                comments = Comment.query.filter_by(recipe_id=recipe.id).all()
                for comment in comments:
                    print(f"Updating comment {comment.id} to point to recipe {recipe_to_keep.id}")
                    comment.recipe_id = recipe_to_keep.id
            
            # Commit changes before deleting recipes
            db.session.commit()
            
            # Now delete the duplicate recipes
            for recipe in recipes_to_delete:
                print(f"Deleting recipe {recipe.id}")
                db.session.delete(recipe)
            
            # Final commit
            db.session.commit()
        
        print("\nFixed all duplicate recipes!")

if __name__ == "__main__":
    fix_duplicate_recipes() 