from app import create_app, db
from app.models import User, Recipe, Ingredient, Comment, Rating, Favorite, ExternalFavorite, ExternalRating, ExternalComment, Tag

app = create_app()
with app.app_context():
    try:
        # Drop all tables
        db.drop_all()
        print("Dropped all tables")
        
        # Create all tables
        db.create_all()
        print("Created all tables")
        
        # Create admin user
        admin = User(
            email='admin@tastebite.com',
            name='Admin',
            is_admin=True
        )
        admin.set_password('admin123')
        db.session.add(admin)
        db.session.commit()
        print("Created admin user")
        
        # Create test user
        test_user = User(
            email='test@tastebite.com',
            name='Test User'
        )
        test_user.set_password('test123')
        db.session.add(test_user)
        db.session.commit()
        print("Created test user")
        
        # Create test recipe
        recipe = Recipe(
            title='Test Recipe',
            category='Test',
            area='Test Area',
            instructions='Test instructions',
            user_id=test_user.id
        )
        db.session.add(recipe)
        db.session.commit()
        print("Created test recipe")
        
        # Add ingredients
        ingredients = [
            Ingredient(name='Ingredient 1', measure='100g', recipe_id=recipe.id),
            Ingredient(name='Ingredient 2', measure='200g', recipe_id=recipe.id)
        ]
        db.session.add_all(ingredients)
        db.session.commit()
        print("Added ingredients")
        
        print("\nDatabase initialized successfully!")
        
    except Exception as e:
        print(f"Error initializing database: {e}")
        db.session.rollback() 