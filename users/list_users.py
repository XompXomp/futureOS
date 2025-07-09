from app import app, db, User

with app.app_context():
    users = User.query.all()
    print(f"{'ID':<5} {'Email':<40} {'Created At'}")
    print('-' * 70)
    for user in users:
        print(f"{user.id:<5} {user.email:<40} {user.created_at}")
    if not users:
        print("No users found.") 