import sys
from app import create_app, db
from app.models import User

def make_admin(email):
    """Make a user an admin by email"""
    app = create_app()
    with app.app_context():
        user = User.query.filter_by(email=email).first()
        if not user:
            print(f"User with email {email} not found.")
            return False
            
        if user.is_admin:
            print(f"User {user.name} is already an admin.")
            return True
            
        user.is_admin = True
        db.session.commit()
        print(f"User {user.name} has been made an admin.")
        return True

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python make_admin.py <email>")
        sys.exit(1)
        
    email = sys.argv[1]
    success = make_admin(email)
    sys.exit(0 if success else 1) 


