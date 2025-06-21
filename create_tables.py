from app import create_app, db
from app.models import User, Recipe, Ingredient, Comment, Rating, Favorite, ExternalFavorite, ExternalRating, ExternalComment, Tag

app = create_app()
with app.app_context():
    db.create_all()
    print('All tables created!') 