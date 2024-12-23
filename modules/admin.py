# File to handle all admin routes
from flask import Blueprint, render_template, request, redirect, url_for, session,flash
from database.init_db import get_db  # Database initialization
from bson import ObjectId

# Create a Blueprint for admin functionalities
admin_bp = Blueprint('admin', __name__, template_folder='admin_templates')
# Initialize the database
db = get_db()

users_collection = db['users']
reviews_collection = db['reviews']
watchlist_collection = db['watchlists']

# Middleware to restrict access to admins only
@admin_bp.before_request
def restrict_to_admins():
    if session.get('role') != 'admin':  # Ensure 'role' is stored in session
        return redirect(url_for('home'))  # Redirect to home if not admin

# Admin Dashboard Route
@admin_bp.route('/dashboard', methods=['GET', 'POST'])
def admin_dashboard():
    if request.method == 'POST':
        # Hypothetical form processing
        new_data = request.form.get('data')
        print(f"New data submitted: {new_data}")

    users_count = users_collection.count_documents({})  # Count all users
    reviews_count = reviews_collection.count_documents({})  # Count all reviews
    return render_template('admin/admin_dashboard.html', users_count=users_count, reviews_count=reviews_count) 

# Manage Users Route
@admin_bp.route('/manage_users')
def manage_users():
    users = users_collection.find({}, {"_id": 1, "username": 1, "email": 1, "role": 1, "watchlist": 1}) 
    return render_template('admin/manage_users.html', users=list(users))

@admin_bp.route('/edit_user/<username>', methods=['POST'])
def edit_user(username):
    new_username = request.form.get('new_username')
    email = request.form.get('email')

    if not new_username or not email:
        flash("Both username and email are required.", "danger")
        return redirect(url_for('admin.manage_users'))

    # Update the user in the database
    users_collection.update_one(
        {"username": username},
        {"$set": {"username": new_username, "email": email}}
    )

    flash(f"User '{username}' updated successfully!", "success")
    return redirect(url_for('admin.manage_users'))

@admin_bp.route('/delete_user/<username>', methods=['POST'])
def delete_user(username):
    users_collection.delete_one({"username": username})
    flash(f"User '{username}' has been deleted successfully!", "success")
    return redirect(url_for('admin.manage_users'))

# Manage Watchlists Route
@admin_bp.route('/manage_watchlists')
def manage_watchlists():
    watchlists = watchlist_collection.find()
    return render_template('admin/manage_watchlists.html', watchlists=watchlists)

@admin_bp.route('/manage_reviews', methods=['GET'])
def manage_reviews():
    # Route to display all user reviews for admin management.
    reviews = list(reviews_collection.find().sort("created_at", -1))  # Sort by newest first
    # Transform reviews for rendering
    reviews_data = [
        {
            "movie_title": review.get("movie_title"),
            "username": review.get("username"),
            "review": review.get("review"),
            "_id": str(review.get("_id")),
        }
        for review in reviews
    ]
    return render_template('admin/manage_reviews.html', reviews=reviews_data)

@admin_bp.route('/delete_review/<review_id>', methods=['POST'])
def delete_review(review_id):
    # Route to delete a review by its ID.
    try:
        reviews_collection.delete_one({"_id": ObjectId(review_id)})
        flash("Review deleted successfully.", "success")
    except Exception as e:
        flash(f"Error deleting review: {e}", "danger")
    return redirect(url_for('admin.manage_reviews'))
    
