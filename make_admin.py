from app import create_app, db
from app.models import User

def make_admin(email):
    """Make a user an admin by email"""
    app = create_app()
    with app.app_context():
        user = User.query.filter_by(email=email).first()
        if user:
            user.is_admin = True
            db.session.commit()
            print(f"User {email} is now an admin!")
        else:
            print(f"User with email {email} not found!")

if __name__ == '__main__':
    import sys
    if len(sys.argv) != 2:
        print("Usage: python make_admin.py <email>")
        sys.exit(1)
    make_admin(sys.argv[1]) 


