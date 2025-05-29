from app import create_app, db

app = create_app()
with app.app_context():
    try:
        # Try to connect to the database
        db.engine.connect()
        print("Successfully connected to the database!")
        print(f"Database URL: {db.engine.url}")
    except Exception as e:
        print(f"Error connecting to the database: {e}") 