from app import create_app, db
from sqlalchemy import inspect

app = create_app()
with app.app_context():
    try:
        inspector = inspect(db.engine)
        tables = inspector.get_table_names()
        print("Tables in database:", tables)
        
        # Check if user table exists and has correct columns
        if 'user' in tables:
            columns = inspector.get_columns('user')
            print("\nColumns in user table:")
            for col in columns:
                print(f"- {col['name']}: {col['type']}")
        else:
            print("\nWARNING: user table not found!")
            
    except Exception as e:
        print(f"Error checking tables: {e}") 