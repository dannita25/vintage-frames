from pymongo import MongoClient
from werkzeug.security import generate_password_hash

def get_db():
    """
    Connect to the MongoDB database and return the database object.
    Ensure MongoDB is running locally at 'localhost:27017'.
    """
    try:
        client = MongoClient('mongodb://localhost:27017/')
        db = client['vintage_frames']  # Replace 'vintage_frames' with your desired database name
        return db
    except Exception as e:
        print(f"Error connecting to MongoDB: {e}")
        raise

def create_admin():
    """ Create an admin user in the 'users' collection if it doesn't already exist.
    The admin user has the role 'admin' and a default password, which should be updated for production. """
    try:
        # Get the database
        db = get_db()
        users_collection = db['users']

        # Check if admin already exists
        if not users_collection.find_one({"username": "admin"}):
            # Create the admin user
            admin_user = {
                "username": "admin",
                "email": "admin@vintageframes.com",
                "password": generate_password_hash("admin25*"),  # Securely hash the password
                "role": "admin"
            }
            users_collection.insert_one(admin_user)
            print("Admin user created successfully!")
        else:
            print("Admin user already exists.")
    except Exception as e:
        print(f"Error creating admin user: {e}")

# Initialize the database 
if __name__ == "__main__":
    create_admin()



