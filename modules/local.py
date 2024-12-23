# File to manage all local spots routes for admin
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from database.init_db import get_db
from bson import ObjectId

# Blueprint for local spot functionalities
local_bp = Blueprint('local', __name__, template_folder='templates')

# Initialize db
db = get_db()
local_spots_collection = db['local_spots']
cinemas_collection = db['cinemas']

# Route to manage local spots
@local_bp.route('/manage_spots', methods=['GET'])
def manage_spots():
    # Fetch all local spots and cinemas
    spots = list(local_spots_collection.find())
    cinemas = list(cinemas_collection.find({}, {"_id": 1, "name": 1}))
    return render_template('admin/manage_spots.html', spots=spots, cinemas=cinemas)

# Route to add a new local spot
@local_bp.route('/add_spot', methods=['POST'])
def add_spot():
    # Get form data
    name = request.form.get('spot_name')
    type = request.form.get('spot_type')
    location = request.form.get('location')
    latitude = request.form.get('latitude')
    longitude = request.form.get('longitude')
    description = request.form.get('description')
    website = request.form.get('website')
    proximity = request.form.getlist('cinema_proximity')  # List of cinema IDs

    if not name or not type or not location or not latitude or not longitude:
        flash("All required fields must be filled out.", "danger")
        return redirect(url_for('local.manage_spots'))

    # Insert into db
    local_spots_collection.insert_one({
        "name": name,
        "type": type,
        "location": location,
        "description": description,
        "website": website,
        "proximity": [ObjectId(cinema_id) for cinema_id in proximity]
    })
    flash(f"Local spot '{name}' added successfully!", "success")
    return redirect(url_for('local.manage_spots'))

# Update an existing local spot
@local_bp.route('/update_spot/<spot_id>', methods=['POST'])
def update_spot(spot_id):
    # Get form data
    name = request.form.get('spot_name')
    type = request.form.get('spot_type')
    location = request.form.get('location')
    latitude = request.form.get('latitude')
    longitude = request.form.get('longitude')
    description = request.form.get('description')
    website = request.form.get('website')

    if not name or not description:
        flash("Name and description are required fields.", "danger")
        return redirect(url_for('local.manage_spots'))

    # Update the spot in db
    local_spots_collection.update_one(
        {"_id": ObjectId(spot_id)},
        {"$set": {
            "name": name,
            "type": type,
            "location": location,
            "latitude": float(latitude),  # Convert to float
            "longitude": float(longitude),  # Convert to float
            "description": description,
            "website": website
        }}
    )
    flash(f"Local spot '{name}' updated successfully!", "success")
    return redirect(url_for('local.manage_spots'))

# Delete a local spot
@local_bp.route('/delete_spot/<spot_id>', methods=['POST'])
def delete_spot(spot_id):
    # Remove the spot from the database
    local_spots_collection.delete_one({"_id": ObjectId(spot_id)})
    flash("Local spot deleted successfully!", "success")
    return redirect(url_for('local.manage_spots'))

# API Route to get local spots near a cinema
@local_bp.route('/get_local_spots/<cinema_id>', methods=['GET'])
def get_local_spots(cinema_id):
    # Find all local spots near a specific cinema
    spots = list(local_spots_collection.find({"proximity": ObjectId(cinema_id)}))
    return jsonify({"spots": spots})
