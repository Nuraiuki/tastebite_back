from app import create_app, db
from app.models import User

app = create_app()
with app.app_context():
    try:
        # Check if admin already exists
        admin = User.query.filter_by(email='admin@tastebite.com').first()
        if not admin:
            admin = User(
                email='admin@tastebite.com',
                name='Admin',
                is_admin=True
            )
            admin.set_password('admin123')
            db.session.add(admin)
            db.session.commit()
            print('Admin user created successfully!')
        else:
            print('Admin user already exists')
    except Exception as e:
        print(f"Error creating admin user: {e}") 