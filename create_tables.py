from app import create_app, db
from app.models import User, Recipe, Ingredient, Comment, Rating, Favorite, ExternalFavorite, ExternalRating, ExternalComment, Tag

app = create_app()
with app.app_context():
    try:
        # Create all tables
        db.create_all()
        print("Successfully created all tables!")
    except Exception as e:
        print(f"Error creating tables: {e}") 