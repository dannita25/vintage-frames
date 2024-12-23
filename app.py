# we run eveything here!
from flask import Flask, flash, render_template, session, redirect, url_for
from database.init_db import get_db  
from modules.extensions import mail
from modules.auth import auth_bp
from modules.admin import admin_bp 
from modules.cinema import cinema_bp
from modules.user_routes import user_routes_bp
from modules.local import local_bp
import os

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'default_secret_key') # Default as a fallback

# Flask-Mail configuration
app.config.update(
    MAIL_SERVER='smtp.gmail.com',  # Replace with correspondent SMTP server
    MAIL_PORT=587,
    MAIL_USE_TLS=True,
    MAIL_USERNAME=os.getenv('MAIL_USERNAME'),  # Used environment variable
    MAIL_PASSWORD=os.getenv('MAIL_PASSWORD')   # Used environment variable
)

mail.init_app(app)  # Initialize Flask-Mail 
# Blueprints
app.register_blueprint(auth_bp, url_prefix='/auth') 
app.register_blueprint(admin_bp, url_prefix='/admin')  
app.register_blueprint(cinema_bp, url_prefix='/cinema')
app.register_blueprint(user_routes_bp, url_prefix='/user_routes')
app.register_blueprint(local_bp, url_prefix='/local')
# Future implementation : input validation and protection against injection attacks.

# Connect to dbs
db = get_db()
users_collection = db['users']
reviews_collection = db['reviews']
watchlist_collection = db['watchlists']
movies_collection = db['movies']  
cinemas_collection = db['cinemas']
local_spots_collection = db['local_spots']
reviews_collection = db['reviews']

@app.route('/test_db')
def test_db():
    user = users_collection.find_one({'username': 'test_user'})
    if user:
        return f"User found: {user['username']}"
    else:
        return "No user found"

@app.route('/')  # Home page route
def home():
    """
    Render the home page with featured films.
    """
    featured_movies = movies_collection.find({}, {
        "_id": 0,
        "title": 1,
        "plot": 1,  #plot serves as the description
        "poster": 1
    }).limit(9)  # Fetch 9 most recent movies

    return render_template('index.html', movies=list(featured_movies))

@app.route('/local_spots')
def local_spots():
    return render_template('local_spots.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/faq')
def faq():
    return render_template('faq.html')

@app.route('/help_support')
def help_support():
    return render_template('help_support.html')

if __name__ == '__main__':
    app.run(debug=True, port=5001)
