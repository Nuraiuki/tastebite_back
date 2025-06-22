# app/routes.py
from flask import Blueprint, request, jsonify, abort, current_app, send_from_directory
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.utils import secure_filename
from datetime import datetime
import traceback
import requests
import json
import os
import logging
import time
from sqlalchemy import func

# Configure logging
logger = logging.getLogger(__name__)

from .models import (
    db, Recipe, Ingredient, User,
    Comment, Rating, Favorite,
    ExternalFavorite, ExternalRating, ExternalComment, ShoppingListItem,
    SharedShoppingList
)
from .utils.openai_client import get_openai_client

bp = Blueprint("recipes", __name__)
bp_ai = Blueprint("ai", __name__, url_prefix="/api/ai")

ALLOWED_EXT = {'png', 'jpg', 'jpeg', 'gif'}
AREAS = [
    "American", "British", "Canadian", "Chinese", "Croatian", "Dutch", 
    "Egyptian", "Filipino", "French", "Greek", "Indian", "Irish", "Italian", 
    "Jamaican", "Japanese", "Kenyan", "Malaysian", "Mexican", "Moroccan", 
    "Polish", "Portuguese", "Russian", "Spanish", "Thai", "Tunisian", 
    "Turkish", "Ukrainian", "Uruguayan", "Vietnamese"
]
CATEGORIES = [
    "Beef", "Chicken", "Dessert", "Lamb", "Miscellaneous", "Pasta", "Pork", 
    "Seafood", "Side", "Starter", "Vegan", "Vegetarian", "Breakfast", "Goat"
]


def allowed_file(fname: str) -> bool:
    return '.' in fname and fname.rsplit('.', 1)[1].lower() in ALLOWED_EXT


# ───────────────  Health  ───────────────
@bp.get("/health")
def health():
    return {
        "status": "ok",
        "timestamp": datetime.utcnow().isoformat()
    }


@bp.get("/routes")
def list_routes():
    return [
        {
            "endpoint": r.endpoint,
            "methods": list(r.methods),
            "path": str(r)
        }
        for r in current_app.url_map.iter_rules()
    ]


# ───────────────  Auth  ───────────────
@bp.post("/auth/register")
def register():
    try:
        data = request.get_json() or {}
        logger.info(f"Registration data: {data}")
        
        for f in ("email", "password", "name"):
            if f not in data:
                logger.warning(f"Missing field: {f}")
                return {"error": f"Missing {f}"}, 400
                
        if User.query.filter_by(email=data["email"]).first():
            logger.warning(f"Email already registered: {data['email']}")
            return {"error": "Email already registered"}, 400

        user = User(email=data["email"], name=data["name"])
        user.set_password(data["password"])
        db.session.add(user)
        db.session.commit()
        login_user(user)
        logger.info(f"User registered successfully: {user.email}")
        return user.to_dict(), 201
    except Exception as e:
        logger.error(f"Registration error: {str(e)}")
        logger.exception("Full traceback:")
        db.session.rollback()
        return {"error": "Internal server error"}, 500


@bp.post("/auth/login")
def login():
    data = request.get_json() or {}
    user = User.query.filter_by(email=data.get("email")).first()
    if user and user.check_password(data.get("password")):
        login_user(user, remember=True)  # Add remember=True for longer session
        logger.info(f"User logged in: {user.email}")
        
        # Create response with user data
        response = jsonify(user.to_dict())
        
        # Add explicit cookie setting for debugging
        if os.environ.get('RENDER') == 'true':
            response.set_cookie(
                'session_debug',
                'logged_in',
                max_age=86400,
                secure=True,
                samesite='None',
                httponly=False
            )
            logger.info("Set debug cookie for production")
        else:
            response.set_cookie(
                'session_debug',
                'logged_in',
                max_age=86400,
                secure=False,
                samesite='Lax',
                httponly=False
            )
            logger.info("Set debug cookie for development")
        
        return response
    logger.warning(f"Failed login attempt for email: {data.get('email')}")
    return {"error": "Invalid email or password"}, 401


@bp.post("/auth/logout")
@login_required
def logout():
    logger.info(f"User logged out: {current_user.email}")
    logout_user()
    return {"message": "Logged out"}


@bp.get("/auth/check")
def auth_check():
    try:
        # Log all cookies for debugging
        logger.info(f"Auth check - All cookies: {dict(request.cookies)}")
        logger.info(f"Auth check - User agent: {request.headers.get('User-Agent')}")
        logger.info(f"Auth check - Origin: {request.headers.get('Origin')}")
        
        if current_user.is_authenticated:
            logger.info(f"Auth check successful for user: {current_user.email}")
            # Добавляем дополнительную проверку сессии
            user = User.query.get(current_user.id)
            if not user:
                logout_user()
                return {"error": "User not found"}, 401
            return user.to_dict()
        logger.warning("Auth check failed - user not authenticated")
        logger.warning(f"Current user: {current_user}")
        logger.warning(f"Session data: {dict(session)}")
        return {"error": "Not authenticated"}, 401
    except Exception as e:
        logger.error(f"Auth check error: {str(e)}")
        logger.exception("Full traceback:")
        return {"error": "Internal server error"}, 500


# ───────────────  Image upload  ───────────────
@bp.post("/upload")
@login_required
def upload():
    if 'image' not in request.files:
        return {"error": "No file part"}, 400
    file = request.files['image']
    if file.filename == '':
        return {"error": "No selected file"}, 400
    if not allowed_file(file.filename):
        return {"error": "File type not allowed"}, 400

    try:
        name = datetime.now().strftime('%Y%m%d_%H%M%S_') + secure_filename(file.filename)
        folder = os.path.join(current_app.static_folder, 'uploads')
        os.makedirs(folder, exist_ok=True)
        file.save(os.path.join(folder, name))
        return {"url": f"https://tastebite-back.onrender.com/static/uploads/{name}"}
    except Exception:
        traceback.print_exc()
        return {"error": "Failed to save file"}, 500


# ───────────────  Recipes  ───────────────
@bp.get("/recipes")
def list_recipes():
    """Get all recipes or filter by external_id"""
    try:
        external_id = request.args.get('external_id')
        logger.info(f"Listing recipes, external_id: {external_id}")
        
        if external_id:
            recipe = Recipe.query.filter_by(external_id=external_id).first()
            if recipe:
                logger.info(f"Found recipe with external_id {external_id}")
                return [recipe.to_dict()]
            logger.info(f"No recipe found with external_id {external_id}")
            return []
            
        recipes = Recipe.query.all()
        logger.info(f"Found {len(recipes)} recipes")
        return [r.to_dict() for r in recipes]
    except Exception as e:
        logger.error(f"Error listing recipes: {str(e)}")
        logger.exception("Full traceback:")
        return {"error": "Internal server error"}, 500


@bp.get("/recipes/<int:rid>")
def one_recipe(rid):
    return Recipe.query.get_or_404(rid).to_dict()


@bp.post("/recipes")
@login_required
def create_recipe():
    data = request.get_json()
    new_recipe = Recipe(
        title=data['title'],
        category=data['category'],
        area=data['area'],
        instructions=data['instructions'],  # Ensure this is handled as Text
        image_url=data['image_url'],
        user_id=current_user.id,
        is_external=False
    )
    
    # Add ingredients
    if "ingredients" in data:
        for ing in data["ingredients"]:
            if isinstance(ing, dict):
                name = ing.get("name", "")
                measure = ing.get("measure", "")
            elif isinstance(ing, str):
                name = ing
                measure = ""
            else:
                continue
            
            if name:  # Only add if name is not empty
                new_recipe.ingredients.append(
                    Ingredient(name=name, measure=measure)
                )
    
    db.session.add(new_recipe)
    db.session.commit()
    return jsonify(new_recipe.to_dict()), 201


@bp.put("/recipes/<int:rid>")
@login_required
def update_recipe(rid):
    """Update an existing recipe"""
    try:
        recipe = Recipe.query.get_or_404(rid)
        
        # Check if user is authorized to edit this recipe
        if recipe.user_id != current_user.id and not current_user.is_admin:
            return jsonify({"error": "Not authorized to edit this recipe"}), 403
        
        data = request.get_json() or {}
        
        # Update basic recipe info
        recipe.title = data.get("title", recipe.title)
        recipe.category = data.get("category", recipe.category)
        recipe.area = data.get("area", recipe.area)
        recipe.instructions = data.get("instructions", recipe.instructions)
        recipe.image_url = data.get("image_url", recipe.image_url)
        
        # Update ingredients
        if "ingredients" in data:
            # Remove existing ingredients
            recipe.ingredients = []
            
            # Add new ingredients
            for ing in data["ingredients"]:
                if isinstance(ing, dict):
                    name = ing.get("name", "")
                    measure = ing.get("measure", "")
                elif isinstance(ing, str):
                    name = ing
                    measure = ""
                else:
                    continue
                
                if name:  # Only add if name is not empty
                    recipe.ingredients.append(
                        Ingredient(name=name, measure=measure)
                    )
        
        db.session.commit()
        return jsonify(recipe.to_dict())
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error updating recipe: {str(e)}")
        return jsonify({"error": "Failed to update recipe"}), 500


@bp.post("/recipes/<int:rid>/rate")
@login_required
def rate_recipe(rid):
    data = request.get_json() or {}
    rating = data.get("rating")
    if rating is None or not isinstance(rating, (int, float)) or rating < 1 or rating > 5:
        return jsonify({"error": "Rating must be a number between 1 and 5"}), 400
    
    try:
        recipe = Recipe.query.get_or_404(rid)
        existing = Rating.query.filter_by(recipe_id=rid, user_id=current_user.id).first()
        
        if existing:
            existing.value = rating
        else:
            new_rating = Rating(recipe_id=rid, user_id=current_user.id, value=rating)
            db.session.add(new_rating)
        
        db.session.commit()
        return jsonify({"message": "Rating saved"})
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error saving rating: {str(e)}")
        return jsonify({"error": "Failed to save rating"}), 500


@bp.post("/recipes/<int:rid>/favorite")
@login_required
def favorite_recipe(rid):
    recipe = Recipe.query.get_or_404(rid)
    existing = Favorite.query.filter_by(recipe_id=rid, user_id=current_user.id).first()
    if existing:
        db.session.delete(existing)
        db.session.commit()
        return {"message": "Removed from favorites"}
    else:
        new_fav = Favorite(recipe_id=rid, user_id=current_user.id)
        db.session.add(new_fav)
        db.session.commit()
        return {"message": "Added to favorites"}


@bp.get("/recipes/<int:rid>/comments")
def get_recipe_comments(rid):
    """Get comments for a recipe"""
    try:
        recipe = Recipe.query.get_or_404(rid)
        # Get all comments for the recipe, ordered by creation date
        comments = Comment.query.filter_by(recipe_id=rid).order_by(Comment.created_at.desc()).all()
        return jsonify([{
            "id": comment.id,
            "content": comment.content,
            "created_at": comment.created_at.isoformat(),
            "user": {
                "id": comment.user.id,
                "name": comment.user.name,
                "email": comment.user.email,
                "avatar": comment.user.avatar
            }
        } for comment in comments])
    except Exception as e:
        current_app.logger.error(f"Error getting recipe comments: {str(e)}")
        return jsonify({"error": "Failed to get comments"}), 500


@bp.post("/recipes/<int:rid>/comments")
@login_required
def add_recipe_comment(rid):
    """Add a comment to a recipe"""
    try:
        recipe = Recipe.query.get_or_404(rid)
        data = request.get_json()
        
        if not data or 'content' not in data:
            return jsonify({"error": "Comment content is required"}), 400
            
        comment = Comment(
            content=data['content'],
            recipe_id=rid,
            user_id=current_user.id
        )
        
        db.session.add(comment)
        db.session.commit()
        
        return jsonify({
            "id": comment.id,
            "content": comment.content,
            "created_at": comment.created_at.isoformat(),
            "user": {
                "id": current_user.id,
                "name": current_user.name,
                "email": current_user.email,
                "avatar": current_user.avatar
            }
        })
    except Exception as e:
        current_app.logger.error(f"Error adding comment: {str(e)}")
        db.session.rollback()
        return jsonify({"error": "Failed to add comment"}), 500


@bp.get("/recipes/<int:rid>/rating")
def get_recipe_rating(rid):
    """Get rating information for a recipe"""
    try:
        recipe = Recipe.query.get_or_404(rid)
        # Get all ratings for the recipe
        ratings = Rating.query.filter_by(recipe_id=rid).all()
        
        # Calculate average rating
        avg_rating = sum(r.value for r in ratings) / len(ratings) if ratings else 0
        
        # Get user's rating if authenticated
        user_rating = None
        if current_user.is_authenticated:
            user_rating_obj = Rating.query.filter_by(
                recipe_id=rid,
                user_id=current_user.id
            ).first()
            if user_rating_obj:
                user_rating = user_rating_obj.value
        
        return jsonify({
            "average": round(avg_rating, 1),
            "count": len(ratings),
            "user_rating": user_rating
        })
    except Exception as e:
        current_app.logger.error(f"Error getting recipe rating: {str(e)}")
        return jsonify({"error": "Failed to get rating"}), 500


@bp.get("/recipes/<int:rid>/favorite")
@login_required
def get_favorite_status(rid):
    favorite = Favorite.query.filter_by(recipe_id=rid, user_id=current_user.id).first()
    return {"is_favorite": favorite is not None}


@bp.delete("/recipes/<int:rid>")
@login_required
def delete_recipe(rid):
    recipe = Recipe.query.get_or_404(rid)
    if recipe.user_id != current_user.id and not current_user.is_admin:
        return {"error": "Not authorized"}, 403
    db.session.delete(recipe)
    db.session.commit()
    return {"message": "Recipe deleted"}


# ───────────────  External lists (MealDB)  ───────────────
@bp.get("/external/categories")
def mealdb_categories():
    try:
        r = requests.get("https://www.themealdb.com/api/json/v1/1/categories.php")
        return [{"id": c["idCategory"], "name": c["strCategory"]} for c in r.json()["categories"]]
    except Exception:
        traceback.print_exc()
        return {"error": "Failed to fetch categories"}, 500


@bp.get("/external/areas")
def mealdb_areas():
    try:
        r = requests.get("https://www.themealdb.com/api/json/v1/1/list.php?a=list")
        return [{"name": m["strArea"]} for m in r.json()["meals"]]
    except Exception:
        traceback.print_exc()
        return {"error": "Failed to fetch areas"}, 500


# ───────────────  Profile  ───────────────
@bp.get("/profile")
@login_required
def get_profile():
    """Get current user's profile"""
    try:
        logger.info(f"Getting profile for user: {current_user.email}")
        user = User.query.get(current_user.id)
        if not user:
            logger.error(f"User not found: {current_user.id}")
            return jsonify({"error": "User not found"}), 404
        
        profile_data = {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "avatar": user.avatar,
            "is_admin": user.is_admin
        }
        logger.info(f"Successfully retrieved profile for user: {user.email}")
        return jsonify(profile_data)
    except Exception as e:
        logger.error(f"Error getting profile: {str(e)}")
        logger.exception("Full traceback:")
        return jsonify({"error": "Internal server error"}), 500

@bp.route("/profile", methods=["GET", "PUT"])
@login_required
def profile():
    if request.method == "GET":
        return jsonify(current_user.to_dict())

    try:
        # Обновление имени и email
        if "name" in request.form:
            current_user.name = request.form["name"]
        if "email" in request.form:
            current_user.email = request.form["email"]

        # Обновление пароля
        if "newPassword" in request.form:
            new_password = request.form["newPassword"]
            if new_password:
                current_user.set_password(new_password)

        # Обновление аватара
        if "avatar" in request.files:
            avatar = request.files["avatar"]
            if avatar and avatar.filename:
                if not allowed_file(avatar.filename):
                    return jsonify({"error": "Invalid file type"}), 400
                    
                # Создаем уникальное имя файла
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f"{current_user.id}_{timestamp}_{secure_filename(avatar.filename)}"
                
                # Убедимся, что директория существует
                upload_folder = os.path.join(current_app.root_path, 'static', 'uploads')
                os.makedirs(upload_folder, exist_ok=True)
                
                # Полный путь к файлу
                avatar_path = os.path.join(upload_folder, filename)
                
                # Сохраняем файл
                avatar.save(avatar_path)
                
                # Обновляем путь к аватару в базе данных
                current_user.avatar = f"/api/static/uploads/{filename}"
                
                logger.info(f"Avatar updated for user {current_user.id}: {current_user.avatar}")

        db.session.commit()
        return jsonify(current_user.to_dict())

    except Exception as e:
        db.session.rollback()
        logger.error(f"Error updating profile: {str(e)}")
        logger.exception("Full traceback:")
        return jsonify({"error": "Failed to update profile"}), 500

@bp.get("/profile/recipes")
@login_required
def get_user_recipes():
    """Get recipes created by current user"""
    try:
        # Получаем только рецепты, созданные пользователем (не импортированные)
        recipes = Recipe.query.filter_by(
            user_id=current_user.id,
            is_external=False  # Исключаем импортированные рецепты
        ).all()
        return jsonify([recipe.to_dict() for recipe in recipes])
    except Exception as e:
        current_app.logger.error(f"Error getting user recipes: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@bp.get("/profile/favorites")
@login_required
def get_user_favorites():
    """Get recipes favorited by current user"""
    try:
        favorites = Favorite.query.filter_by(user_id=current_user.id).all()
        recipes = [Recipe.query.get(fav.recipe_id) for fav in favorites]
        return jsonify([recipe.to_dict() for recipe in recipes if recipe])
    except Exception as e:
        current_app.logger.error(f"Error getting user favorites: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@bp.get("/profile/ratings")
@login_required
def get_user_ratings():
    """Get ratings given by current user"""
    try:
        ratings = Rating.query.filter_by(user_id=current_user.id).all()
        return jsonify([{
            "id": rating.id,
            "value": rating.value,
            "recipe": Recipe.query.get(rating.recipe_id).to_dict() if Recipe.query.get(rating.recipe_id) else None
        } for rating in ratings])
    except Exception as e:
        current_app.logger.error(f"Error getting user ratings: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@bp.get("/profile/stats")
@login_required
def get_user_stats():
    """Get user statistics"""
    try:
        logger.info(f"Getting stats for user: {current_user.email}")
        
        # Get total recipes created (excluding imported ones)
        total_recipes = Recipe.query.filter_by(
            user_id=current_user.id,
            is_external=False  # Only count created recipes
        ).count()
        
        # Get total favorites
        total_favorites = Favorite.query.filter_by(user_id=current_user.id).count()
        
        # Get total ratings given by user
        total_ratings = Rating.query.filter_by(user_id=current_user.id).count()
        
        # Get total comments
        total_comments = Comment.query.filter_by(user_id=current_user.id).count()
        
        stats = {
            "total_recipes": total_recipes,
            "total_favorites": total_favorites,
            "total_ratings": total_ratings,
            "total_comments": total_comments
        }
        
        logger.info(f"Successfully retrieved stats for user: {current_user.email}")
        return jsonify(stats)
    except Exception as e:
        logger.error(f"Error getting user stats: {str(e)}")
        logger.exception("Full traceback:")
        return jsonify({"error": "Failed to get user stats"}), 500

@bp.delete("/profile/favorites/<int:recipe_id>")
@login_required
def remove_from_favorites(recipe_id):
    favorite = Favorite.query.filter_by(
        recipe_id=recipe_id,
        user_id=current_user.id
    ).first_or_404()
    db.session.delete(favorite)
    db.session.commit()
    return {"message": "Removed from favorites"}

@bp.delete("/profile")
@login_required
def delete_own_account():
    """Delete current user's account and all their content"""
    try:
        user_id = current_user.id
        
        # Delete all user's content
        Recipe.query.filter_by(user_id=user_id).delete()
        Rating.query.filter_by(user_id=user_id).delete()
        Favorite.query.filter_by(user_id=user_id).delete()
        Comment.query.filter_by(user_id=user_id).delete()
        
        # Delete the user
        db.session.delete(current_user)
        db.session.commit()
        
        # Logout the user
        logout_user()
        
        return jsonify({"message": "Account and all content deleted successfully"})
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error deleting account: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500


# ───────────────  Admin  ───────────────
@bp.get("/admin/users")
@login_required
def get_users():
    """Get all users with their stats (admin only)"""
    if not current_user.is_admin:
        return jsonify({"error": "Unauthorized"}), 403
    
    try:
        users = User.query.all()
        return jsonify([{
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "is_admin": user.is_admin,
            "stats": {
                "recipes_count": Recipe.query.filter_by(
                    user_id=user.id,
                    is_external=False  # Only count created recipes
                ).count(),
                "favorites_count": Favorite.query.filter_by(user_id=user.id).count(),
                "ratings_count": Rating.query.filter_by(user_id=user.id).count(),
                "comments_count": Comment.query.filter_by(user_id=user.id).count()
            },
            "created_at": user.created_at.isoformat() if hasattr(user, 'created_at') else None
        } for user in users])
    except Exception as e:
        current_app.logger.error(f"Error getting users: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@bp.get("/admin/recipes")
@login_required
def get_all_recipes():
    """Get all recipes with user info (admin only)"""
    if not current_user.is_admin:
        return jsonify({"error": "Unauthorized"}), 403
    
    try:
        # Get only created recipes (not imported)
        recipes = Recipe.query.filter_by(is_external=False).all()
        return jsonify([{
            **recipe.to_dict(),
            "author": {
                "id": recipe.author.id,
                "name": recipe.author.name,
                "email": recipe.author.email
            } if recipe.author else None,
            "stats": {
                "ratings_count": Rating.query.filter_by(recipe_id=recipe.id).count(),
                "favorites_count": Favorite.query.filter_by(recipe_id=recipe.id).count(),
                "comments_count": Comment.query.filter_by(recipe_id=recipe.id).count(),
                "average_rating": recipe.average_rating()
            }
        } for recipe in recipes])
    except Exception as e:
        current_app.logger.error(f"Error getting recipes: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@bp.delete("/admin/users/<int:user_id>")
@login_required
def delete_user(user_id):
    """Delete a user and all their content (admin only)"""
    if not current_user.is_admin:
        return jsonify({"error": "Unauthorized"}), 403
    
    if user_id == current_user.id:
        return jsonify({"error": "Cannot delete yourself"}), 400
    
    try:
        user = User.query.get(user_id)
        if not user:
            return jsonify({"error": "User not found"}), 404
        
        # Delete all user's content
        Recipe.query.filter_by(user_id=user_id).delete()
        Rating.query.filter_by(user_id=user_id).delete()
        Favorite.query.filter_by(user_id=user_id).delete()
        Comment.query.filter_by(user_id=user_id).delete()
        
        # Delete the user
        db.session.delete(user)
        db.session.commit()
        
        return jsonify({"message": "User and all their content deleted successfully"})
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error deleting user: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@bp.delete("/admin/recipes/<int:recipe_id>")
@login_required
def delete_recipe_admin(recipe_id):
    """Delete a recipe (admin only)"""
    if not current_user.is_admin:
        return jsonify({"error": "Unauthorized"}), 403
    
    try:
        recipe = Recipe.query.get(recipe_id)
        if not recipe:
            return jsonify({"error": "Recipe not found"}), 404
        
        # Delete all related content
        Rating.query.filter_by(recipe_id=recipe_id).delete()
        Favorite.query.filter_by(recipe_id=recipe_id).delete()
        Comment.query.filter_by(recipe_id=recipe_id).delete()
        
        # Delete the recipe
        db.session.delete(recipe)
        db.session.commit()
        
        return jsonify({"message": "Recipe and all related content deleted successfully"})
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error deleting recipe: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@bp.get("/admin/stats")
@login_required
def get_admin_stats():
    """Get overall statistics (admin only)"""
    if not current_user.is_admin:
        return jsonify({"error": "Unauthorized"}), 403
    
    try:
        # Get total users
        total_users = User.query.count()
        
        # Get total created recipes
        total_created_recipes = Recipe.query.filter_by(is_external=False).count()
        
        # Get total external recipes
        total_external_recipes = Recipe.query.filter_by(is_external=True).count()
        
        # Get total recipes (created + external)
        total_recipes = total_created_recipes + total_external_recipes
        
        # Get total ratings
        total_ratings = Rating.query.count()
        
        # Get total favorites
        total_favorites = Favorite.query.count()
        
        # Get total comments
        total_comments = Comment.query.count()
        
        # Calculate average rating using the correct field name 'value'
        avg_rating = db.session.query(func.avg(Rating.value)).scalar() or 0

        # Get most active users
        users = User.query.all()
        active_users = sorted(
            [{
                "id": u.id,
                "name": u.name,
                "email": u.email,
                "recipes_count": Recipe.query.filter_by(user_id=u.id, is_external=False).count(),
                "ratings_count": Rating.query.filter_by(user_id=u.id).count(),
                "favorites_count": Favorite.query.filter_by(user_id=u.id).count()
            } for u in users],
            key=lambda x: (x["recipes_count"], x["ratings_count"], x["favorites_count"]),
            reverse=True
        )[:5]
        
        return jsonify({
            'total_users': total_users,
            'total_recipes': total_recipes,
            'user_created_recipes': total_created_recipes,
            'external_recipes': total_external_recipes,
            'total_ratings': total_ratings,
            'total_favorites': total_favorites,
            'total_comments': total_comments,
            'average_rating': float(avg_rating),
            'active_users': active_users
        })
    except Exception as e:
        current_app.logger.error(f"Error getting admin stats: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@bp.post("/admin/users/<int:user_id>/toggle-admin")
@login_required
def toggle_admin_status(user_id):
    """Toggle admin status for a user (admin only)"""
    if not current_user.is_admin:
        return jsonify({"error": "Unauthorized"}), 403
    
    if user_id == current_user.id:
        return jsonify({"error": "Cannot change your own admin status"}), 400
    
    try:
        user = User.query.get(user_id)
        if not user:
            return jsonify({"error": "User not found"}), 404
        
        user.is_admin = not user.is_admin
        db.session.commit()
        
        return jsonify({
            "message": f"User {'promoted to' if user.is_admin else 'demoted from'} admin",
            "user": {
                "id": user.id,
                "name": user.name,
                "email": user.email,
                "is_admin": user.is_admin
            }
        })
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error toggling admin status: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500


# ───────────────────────────────────────────────────────────────
#  AI Blueprint
# ───────────────────────────────────────────────────────────────
@bp_ai.post("/generate-recipe")
@login_required          # уберите, если гостям тоже можно
def ai_generate():
    payload = request.get_json() or {}
    items = payload.get("ingredients", [])
    if not items:
        return {"error": "No ingredients provided"}, 400

    areas_str = ", ".join(AREAS)
    categories_str = ", ".join(CATEGORIES)
    ingredients_str = ", ".join(items)

    prompt = (
        f"Based on the following ingredients: {ingredients_str}. "
        f"Generate a detailed recipe. The entire response, including title and instructions, "
        f"must be in the same language as the ingredients provided. "
        f"Return a JSON object with the fields: 'title' (string), 'category' (string), "
        f"'area' (string), 'ingredients' (a list of objects, where each object has 'name' and 'measure' keys), "
        f"and 'instructions' (string with steps separated by '\\n'). "
        f"The 'category' value must be one of the following: {categories_str}. "
        f"The 'area' value must be one of the following: {areas_str}. "
        f"The JSON response should not contain any comments."
    )

    try:
        client = get_openai_client()
        rsp = client.chat.completions.create(
            model="gpt-4o-mini",
            temperature=0.7,
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
        )
        recipe_data = json.loads(rsp.choices[0].message.content)

        # Убедимся, что instructions - это строка
        if isinstance(recipe_data.get("instructions"), list):
            recipe_data["instructions"] = "\\n".join(map(str, recipe_data["instructions"]))
        
        return jsonify(recipe_data)
    except Exception as e:
        traceback.print_exc()
        return {"error": str(e)}, 500


@bp.post("/import-external-recipe")
@login_required
def import_external_recipe():
    """Import a recipe from external source (MealDB)"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400

        # Check if recipe with this external_id already exists for ANY user
        existing_recipe = Recipe.query.filter_by(
            external_id=data.get('externalId')
        ).first()

        if existing_recipe:
            # If recipe exists, return it without creating a new copy
            return jsonify(existing_recipe.to_dict())

        # Create new recipe only if it doesn't exist
        recipe = Recipe(
            title=data['title'],
            category=data.get('category'),
            area=data.get('area'),
            instructions=data['instructions'],
            image_url=data.get('imageUrl'),
            user_id=current_user.id,
            is_external=True,
            external_id=data.get('externalId')
        )

        # Add ingredients
        for ing in data.get('ingredients', []):
            recipe.ingredients.append(
                Ingredient(
                    name=ing['name'],
                    measure=ing.get('measure', '')
                )
            )

        db.session.add(recipe)
        db.session.commit()

        return jsonify(recipe.to_dict()), 201

    except Exception as e:
        current_app.logger.error(f"Error importing external recipe: {str(e)}")
        db.session.rollback()
        return jsonify({"error": "Failed to import recipe"}), 500


@bp.route('/static/uploads/<filename>')
def uploaded_file(filename):
    """Serve uploaded files"""
    return send_from_directory(os.path.join(current_app.root_path, 'static', 'uploads'), filename)


@bp.get("/users/<int:user_id>")
def get_user_profile(user_id):
    """Get another user's profile"""
    try:
        user = User.query.get(user_id)
        if not user:
            return jsonify({"error": "User not found"}), 404
        
        profile_data = {
            "id": user.id,
            "name": user.name,
            "avatar": user.avatar,
            "created": user.created_at.isoformat() if hasattr(user, 'created_at') else None
        }
        return jsonify(profile_data)
    except Exception as e:
        logger.error(f"Error getting user profile: {str(e)}")
        logger.exception("Full traceback:")
        return jsonify({"error": "Internal server error"}), 500

@bp.get("/users/<int:user_id>/recipes")
def get_other_user_recipes(user_id):
    """Get recipes created by another user"""
    try:
        recipes = Recipe.query.filter_by(
            user_id=user_id,
            is_external=False
        ).all()
        return jsonify([recipe.to_dict() for recipe in recipes])
    except Exception as e:
        logger.error(f"Error getting user recipes: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

# ─────────────── Shopping List ───────────────

@bp.get("/shopping-list")
@login_required
def get_shopping_list():
    """Get all items in the user's shopping list"""
    items = ShoppingListItem.query.filter_by(user_id=current_user.id).all()
    return jsonify([item.to_dict() for item in items])

@bp.post("/shopping-list/add-recipe/<int:recipe_id>")
@login_required
def add_recipe_to_shopping_list(recipe_id):
    """Add all ingredients from a recipe to the shopping list, merging duplicates."""
    recipe = Recipe.query.get_or_404(recipe_id)
    
    # Получаем текущий список покупок пользователя
    shopping_list_items = ShoppingListItem.query.filter_by(user_id=current_user.id).all()
    # Создаем словарь для быстрого доступа по имени ингредиента
    current_shopping_list = {item.name.lower(): item for item in shopping_list_items}
    
    added_count = 0
    updated_count = 0

    for ingredient in recipe.ingredients:
        item_name_lower = ingredient.name.lower()
        
        if item_name_lower in current_shopping_list:
            # Ингредиент уже есть - обновляем его
            existing_item = current_shopping_list[item_name_lower]
            
            # Обновляем список названий
            titles = existing_item.recipe_titles.split('; ') if existing_item.recipe_titles else []
            if recipe.title not in titles:
                titles.append(recipe.title)
                existing_item.recipe_titles = "; ".join(titles)

            # Обновляем список ID
            ids = existing_item.recipe_ids.split('; ') if existing_item.recipe_ids else []
            if str(recipe.id) not in ids:
                ids.append(str(recipe.id))
                existing_item.recipe_ids = "; ".join(ids)

            # Обновляем список мер
            measures = existing_item.measure.split('; ') if existing_item.measure else []
            if ingredient.measure and ingredient.measure not in measures:
                measures.append(ingredient.measure)
                existing_item.measure = "; ".join(measures)
            
            updated_count += 1
        else:
            # Ингредиента нет - создаем новый
            item = ShoppingListItem(
                name=ingredient.name,
                measure=ingredient.measure or '',
                recipe_titles=recipe.title,
                recipe_ids=str(recipe.id),
                user_id=current_user.id
            )
            db.session.add(item)
            added_count += 1
    
    db.session.commit()
    
    return jsonify({
        "message": f"Shopping list updated: {added_count} new items added, {updated_count} items updated."
    })

@bp.delete("/shopping-list")
@login_required
def clear_shopping_list():
    """Clear all items from the user's shopping list"""
    ShoppingListItem.query.filter_by(user_id=current_user.id).delete()
    db.session.commit()
    return jsonify({"message": "Shopping list cleared."})

@bp.delete("/shopping-list/<int:item_id>")
@login_required
def delete_shopping_list_item(item_id):
    """Delete a specific item from the shopping list"""
    item = ShoppingListItem.query.filter_by(id=item_id, user_id=current_user.id).first_or_404()
    db.session.delete(item)
    db.session.commit()
    return jsonify({"message": "Item removed from shopping list."})

@bp.put("/shopping-list/<int:item_id>/toggle")
@login_required
def toggle_shopping_list_item(item_id):
    """Toggle the is_checked status of a shopping list item"""
    item = ShoppingListItem.query.filter_by(id=item_id, user_id=current_user.id).first_or_404()
    item.is_checked = not item.is_checked
    db.session.commit()
    return jsonify(item.to_dict())

# ─────────────── Sharing ───────────────

@bp.post("/shopping-list/share")
@login_required
def share_shopping_list():
    """Generate a shareable link for the user's shopping list."""
    # Ищем существующую ссылку или создаем новую
    shared_list = SharedShoppingList.query.filter_by(user_id=current_user.id).first()
    if not shared_list:
        shared_list = SharedShoppingList(user_id=current_user.id)
        db.session.add(shared_list)
        db.session.commit()
    return jsonify(shared_list.to_dict())

@bp.get("/public/shopping-list/<string:token>")
def get_public_shopping_list(token):
    """Get a shopping list via a public token."""
    shared_list = SharedShoppingList.query.filter_by(token=token).first_or_404()
    
    # Получаем сам список покупок
    items = ShoppingListItem.query.filter_by(user_id=shared_list.user_id).all()
    
    # Получаем имя владельца списка
    owner_name = shared_list.user.name
    
    return jsonify({
        "owner_name": owner_name,
        "items": [item.to_dict() for item in items]
    })

# экспорт для create_app
__all__ = ["bp", "bp_ai"]
