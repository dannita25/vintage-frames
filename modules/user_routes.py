# File to handle frontend user actions
from datetime import datetime
from flask import Blueprint, jsonify, request, render_template, session, jsonify, flash, redirect, url_for
from database.init_db import get_db
from werkzeug.security import generate_password_hash


user_routes_bp = Blueprint('user_routes', __name__, template_folder = 'templates')

# Database initialization
db = get_db()
screenings_collection = db['screenings']
movies_collection = db['movies']   
cinemas_collection = db['cinemas']
watchlists_collection = db['watchlists']
users_collection = db['users']
local_spots_collection = db['local_spots']
reviews_collection = db['reviews']

@user_routes_bp.route('/screenings', methods=['GET'])
def screenings():
    """
    Render the Screenings page with active screenings, enriched with data from movies and cinemas,
    and handle filtering logic.
    """

    # Base query to fetch active screenings
    query = {"status": "active"}

    # Apply filters if they are passed as query parameters
    date_filter = request.args.get("date")
    location_filter = request.args.get("location")
    genre_filter = request.args.get("genre")

    # Apply date filter
    if date_filter:
        query["screening_datetime"] = {"$regex": date_filter}

    # Apply location filter
    if location_filter:
        query["cinema_name"] = location_filter

    # Apply genre filter
    if genre_filter:
        query["movie_title"] = {"$in": [
            movie["title"] for movie in movies_collection.find(
                {"genre": {"$regex": genre_filter, "$options": "i"}}, {"title": 1})
        ]}

    # Fetch all screenings based on the query
    screenings = list(
        screenings_collection.find(
            query,
            {
                "_id": 0,
                "movie_title": 1,
                "cinema_name": 1,
                "screening_datetime": 1,
                "screening_format": 1,
                "ticket_link": 1,
                "special_notes": 1,
                "status": 1
            }
        )
    )

    # Screenings additional details
    for screening in screenings:
        # Fetch and attach movie details
        screening["movie_details"] = movies_collection.find_one(
            {"title": screening["movie_title"]},
            {"_id": 0, "title": 1, "genre": 1, "plot": 1, "poster": 1}
        )

        # Fetch and attach cinema details
        screening["cinema_details"] = cinemas_collection.find_one(
            {"name": screening["cinema_name"]},
            {"_id": 0, "name": 1, "location": 1, "website": 1}
        )

    # Fetch unique genres for the dropdown menu
    genres = set()
    locations = set()
    for movie in movies_collection.find({}, {"genre": 1}):
        if "genre" in movie:
            genres.update([g.strip() for g in movie["genre"].split(",")])

    # Fetch unique locations for the dropdown menu
    locations.update(cinema["name"] for cinema in cinemas_collection.find({}, {"name": 1}))

    # Render the page with screenings and filter options
    return render_template(
        "screenings.html",
        screenings=screenings,
        genres=sorted(genres) if genres else [],
        locations=sorted(locations) if locations else [], #fallback
        selected_date=date_filter,
        selected_location=location_filter,
        selected_genre=genre_filter
    )

@user_routes_bp.route('/bookmark', methods=['POST'])
def toggle_bookmark():

    if not session.get('username'):
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json()
    print(f"Received bookmark request: {data}")
    movie_title = data.get('movie_title')
    bookmark = data.get('bookmark')  # True to bookmark, False to unbookmark

    if not movie_title:
        return jsonify({"error": "Missing movie_title"}), 400

    # Update the user's watchlist
    user = users_collection.find_one({"username": session['username']})
    if not user:
        return jsonify({"error": "User not found"}), 404

    if bookmark:
        # Add to watchlist if not already there
        if movie_title not in user.get('watchlist', []):
            users_collection.update_one(
                {"username": session['username']},
                {"$addToSet": {"watchlist": movie_title}}
            )
    else:
        # Remove from watchlist
        users_collection.update_one(
            {"username": session['username']},
            {"$pull": {"watchlist": movie_title}}
        )
    return jsonify({"success": True})

@user_routes_bp.route('/watchlist', methods=['GET'])
def watchlist():
    return render_template('watchlist.html')

@user_routes_bp.route('/get_watchlist', methods=['GET'])
def get_watchlist():
    if not session.get('username'):
        return jsonify({"error": "Unauthorized"}), 401

    user = users_collection.find_one({"username": session['username']})
    if not user:
        return jsonify({"error": "User not found"}), 404

    # Ensure watchlist contains valid ObjectIds
    watchlist = user.get("watchlist", [])
    if not watchlist:
        return jsonify({"watchlist": []})  # Return empty list if no watchlist

    # Fetch full movie details
    movies = movies_collection.find({"title": {"$in": watchlist}})
    movie_list = [{"title": movie["title"]} for movie in movies]

    return jsonify({"watchlist": movie_list})



@user_routes_bp.route('/local_spots', methods=['GET'])
def local_spots():
    """
    Route to render the Local Vintage Spots page with the list of spots and cinemas.
    """
    # Fetch all local spots and cinemas from db
    local_spots = list(local_spots_collection.find())
    cinemas = list(cinemas_collection.find({}, {"_id": 1, "name": 1, "latitude": 1, "longitude": 1}))

    # Transform spots data for the frontend
    spots_data = [
        {
            "name": spot.get("name"),
            "type": spot.get("type"),
            "location": spot.get("location"),
            "latitude": spot.get("latitude"),
            "longitude": spot.get("longitude"),
            "description": spot.get("description"),
            "website": spot.get("website"),
            "proximity": spot.get("proximity")  # Cinema IDs close by spot
        }
        for spot in local_spots
    ]
   
   # Transform cinemas for the frontend   
    cinema_data = [
        {
            "name": cinema.get("name"),
            "latitude": cinema.get("latitude"),
            "longitude": cinema.get("longitude")
        }
        for cinema in cinemas
    ]

    # Render the HTML with the local spots data
    return render_template('local_spots.html', spots=spots_data, cinemas=cinema_data)

@user_routes_bp.route('/movie/<movie_title>/reviews', methods=['GET', 'POST'])
def movie_reviews(movie_title):
    """
    Route to display movie details, user reviews, and a form to leave a review.
    """
    # Fetch movie details
    movie = movies_collection.find_one({"title": movie_title})
    if not movie:
        flash("Movie not found!", "danger")
        return redirect(url_for('user_routes.screenings'))

    # Fetch reviews for this movie
    reviews = reviews_collection.find({"movie_title": movie_title}).sort("created_at", -1)  # Newest reviews first
    reviews_data = [
        {
            "username": review.get("username"),
            "review": review.get("review"),
            "created_at": review.get("created_at").strftime("%Y-%m-%d %H:%M") if review.get("created_at") else None
        }
        for review in reviews
    ]

    if request.method == 'POST':

        # Check if the user is logged in
        if 'username' not in session:
            flash("You need to be logged in to leave a review.", "warning")
            return redirect(url_for('auth.login'))
        
        # Handle review submission
        username = session.get('username')
        review_text = request.form.get('review')
        if not review_text:
            flash("Review text cannot be empty.", "danger")
        else:
            new_review = {
                "movie_title": movie_title,
                "username": username,
                "review": review_text,
                "created_at": datetime.utcnow(),
            }
            reviews_collection.insert_one(new_review)
            flash("Your review has been added!", "success")
            return redirect(url_for('user_routes.movie_reviews', movie_title=movie_title))

    return render_template(
        'movie_reviews.html',
        movie=movie,
        reviews=reviews_data,
        is_logged_in=('username' in session)
    )

@user_routes_bp.route('/my_reviews', methods=['GET'])
def user_reviews():
    # Route to display reviews submitted by the logged-in user.

    username = session.get('username')
    if not username:
        return redirect(url_for('auth.login'))

    # Fetch reviews written by the user
    user_reviews = reviews_collection.find({"username": username}).sort("created_at", -1)
    reviews_data = [
        {
            "movie_title": review.get("movie_title"),
            "review": review.get("review"),
            "created_at": review.get("created_at").strftime("%Y-%m-%d %H:%M") if review.get("created_at") else None
        }
        for review in user_reviews
    ]

    return render_template('user_reviews.html', reviews=reviews_data)

@user_routes_bp.route('/profile', methods=['GET'])
def profile_settings():
    """
    Render the Profile Settings page.
    """
    username = session.get('username')
    if not username:
        flash("You need to be logged in to view your profile.", "warning")
        return redirect(url_for('auth.login'))

    # Fetch user data from the database
    user = users_collection.find_one({"username": username})
    if not user:
        flash("User not found!", "danger")
        return redirect(url_for('auth.login'))

    # Pass user data to the profile.html template
    return render_template('profile.html', user=user)

@user_routes_bp.route('/profile/update', methods=['POST'])
def update_account():
    """
    Handle account settings updates from profile.html.
    """
    username = session.get('username')
    if not username:
        flash("You need to be logged in to update your profile.", "warning")
        return redirect(url_for('auth.login'))

    # Fetch user data
    user = users_collection.find_one({"username": username})
    if not user:
        flash("User not found!", "danger")
        return redirect(url_for('auth.login'))

    # Get form data from the profile.html form
    new_username = request.form.get('username').strip()
    new_email = request.form.get('email').strip()
    new_password = request.form.get('password').strip()
    confirm_password = request.form.get('confirm_password').strip()

    # Validate and update
    updates = {}
    if new_username and new_username != user['username']:
        updates['username'] = new_username
    if new_email and new_email != user['email']:
        updates['email'] = new_email
    if new_password:
        if new_password != confirm_password:
            flash("Passwords do not match!", "danger")
            return redirect(url_for('user_routes.profile_settings'))
        updates['password'] = generate_password_hash(new_password)

    if updates:
        users_collection.update_one({"_id": user["_id"]}, {"$set": updates})
        flash("Account updated successfully!", "success")
        if 'username' in updates:
            session['username'] = updates['username']  # Update session username
    else:
        flash("No changes were made.", "info")

    return redirect(url_for('user_routes.profile_settings'))





 
