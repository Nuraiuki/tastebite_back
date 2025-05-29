from app import create_app, db
from app.models import User, Recipe, Ingredient, Comment, Rating, Favorite, ExternalFavorite, ExternalRating, ExternalComment, Tag
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = create_app()
with app.app_context():
    try:
        # Log database URL (without password)
        db_url = app.config["SQLALCHEMY_DATABASE_URI"]
        safe_url = db_url.replace(db_url.split("@")[0], "***")
        logger.info(f"Using database: {safe_url}")
        
        # Drop all tables
        logger.info("Dropping all tables...")
        db.drop_all()
        logger.info("All tables dropped successfully")
        
        # Create all tables
        logger.info("Creating all tables...")
        db.create_all()
        logger.info("All tables created successfully")
        
        # Create admin user
        logger.info("Creating admin user...")
        admin = User(
            email='admin@tastebite.com',
            name='Admin',
            is_admin=True
        )
        admin.set_password('admin123')
        db.session.add(admin)
        db.session.commit()
        logger.info("Admin user created successfully")
        
        # Create test user
        logger.info("Creating test user...")
        test_user = User(
            email='test@tastebite.com',
            name='Test User'
        )
        test_user.set_password('test123')
        db.session.add(test_user)
        db.session.commit()
        logger.info("Test user created successfully")
        
        # Create test recipe
        logger.info("Creating test recipe...")
        recipe = Recipe(
            title='Test Recipe',
            category='Test',
            area='Test Area',
            instructions='Test instructions',
            user_id=test_user.id
        )
        db.session.add(recipe)
        db.session.commit()
        logger.info("Test recipe created successfully")
        
        # Add ingredients
        logger.info("Adding ingredients...")
        ingredients = [
            Ingredient(name='Ingredient 1', measure='100g', recipe_id=recipe.id),
            Ingredient(name='Ingredient 2', measure='200g', recipe_id=recipe.id)
        ]
        db.session.add_all(ingredients)
        db.session.commit()
        logger.info("Ingredients added successfully")
        
        logger.info("\nDatabase initialized successfully!")
        
    except Exception as e:
        logger.error(f"Error initializing database: {str(e)}")
        logger.exception("Full traceback:")
        db.session.rollback() 