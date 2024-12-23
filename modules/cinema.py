from flask import Blueprint, render_template, request, redirect, url_for, flash
from database.init_db import get_db 
from modules.omdb_api import fetch_movie_data
from datetime import datetime

# Blueprint for cinema functionalities
cinema_bp = Blueprint('cinema', __name__, template_folder='templates/admin') 

# Database initialization
db = get_db()

# DB tables
screenings_collection = db['screenings']   
movies_collection = db['movies']    
cinemas_collection = db['cinemas']  
watchlists_collection = db['watchlists']

# Retrieve data for movies with OMBd API

@cinema_bp.route('/fetch_movie', methods=['POST'])
def fetch_movie():
    # Purpose: Fetch movie data from OMDb and add / update db
    title = request.form.get('title')
    if not title:
        flash("Please enter a movie title.", "danger")
        return redirect(url_for('cinema.manage_omdb'))
    
    movie_data = fetch_movie_data(title)
    if "error" in movie_data:
        flash(movie_data['error'], "danger")
    else:
        # Insert movie data if it doesn't exist yet
        result = movies_collection.update_one(
            {"title": movie_data['title']},
            {"$set": movie_data},
            upsert=True
        )
        if result.upserted_id:
            flash(f"Movie '{movie_data['title']}' added successfully!", "success")
        else:
            flash(f"Movie '{movie_data['title']}' already exists and was updated.", "info")

    return redirect(url_for('cinema.manage_omdb'))



@cinema_bp.route('/delete_movie/<source>/<title>', methods=['POST'])
def delete_movie(source, title):
    """
    Delete a movie from the specified collection.
    :param source: The source collection ('omdb' or 'cinema').
    :param title: The title of the movie to delete.
    """
    if source == 'omdb':
        result = movies_collection.delete_one({"title": title})
        if result.deleted_count:
            flash(f"Movie '{title}' deleted successfully!", "success")
        else:
            flash(f"Movie '{title}' not found.", "danger")
        return redirect(url_for('cinema.manage_omdb'))
    else:
        flash("Invalid source specified.", "danger")
        return redirect(url_for('cinema.manage_omdb'))


@cinema_bp.route('/manage_omdb', methods=['GET'])
def manage_omdb():
    # Display all movies fetched from OMDb.
    stored_movies = movies_collection.find({}, {
        "_id": 0, 
        "title": 1, 
        "year": 1, 
        "genre": 1,
        "director": 1,
        "actors": 1,
        "plot": 1,
        "poster": 1,
        "imdb_rating": 1,})
    return render_template('admin/manage_omdb.html', stored_movies=list(stored_movies))


# Manage Cinemas db
@cinema_bp.route('/manage', methods=['GET', 'POST'])
def manage_cinemas():
    # View and add cinemas to the database.
    # GET: Display all cinemas in the database.
    # POST: Add a new cinema to the database. 
    if request.method == 'POST':
        # Get data from the form
        name = request.form.get('name')
        description = request.form.get('description')
        location = request.form.get('location')
        latitude = request.form.get('latitude')
        longitude = request.form.get('longitude')
        website = request.form.get('website')
        special_notes = request.form.get('special_notes')

        # Validation check
        if not (name and location and latitude and longitude and website):
            flash("All fields are required to add a cinema.", "danger")
            return redirect(url_for('cinema.manage_cinemas'))

        # Insert new cinema
        cinemas_collection.insert_one({
            "name": name.strip(),
            "description": description.strip(),
            "location": location.strip(),
            "latitude": latitude.strip(),
            "longitude": longitude.strip(),
            "website": website.strip(),
            "special_notes": special_notes.strip()
        })
        flash(f"Cinema '{name}' added successfully!", "success")
        return redirect(url_for('cinema.manage_cinemas'))

    # GET: Fetch all cinemas
    all_cinemas = list(cinemas_collection.find({}, {"_id": 0}))
    return render_template('admin/manage_cinemas.html', cinemas=all_cinemas)

# Delete a Cinema
@cinema_bp.route('/delete/<name>', methods=['POST'])
def delete_cinema(name):
    """
    Delete a cinema from the database.
    """
    result = cinemas_collection.delete_one({"name": name})
    if result.deleted_count:
        flash(f"Cinema '{name}' deleted successfully.", "success")
    else:
        flash(f"Cinema '{name}' not found.", "danger")
    return redirect(url_for('cinema.manage_cinemas'))

# Update a Cinema
@cinema_bp.route('/update/<name>', methods=['POST'])
def update_cinema(name):
    """
    Update an existing cinema's details.
    """
    updated_name = request.form.get('name')
    updated_description = request.form.get('description')
    updated_location = request.form.get('location')
    updated_latitude = request.form.get('latitude')
    updated_longitude = request.form.get('longitude')
    updated_website = request.form.get('website')
    updated_special_notes = request.form.get('special_notes')

    # Validation check
    if not all([updated_name, updated_location, updated_latitude, updated_longitude, updated_website]):
        flash("All fields are required to update the cinema.", "danger")
        return redirect(url_for('cinema.update_cinema'))

    # Update the cinema
    cinemas_collection.update_one(
        {"name": name},
        {"$set": {
            "name": updated_name.strip(),
            "description": updated_description.strip(),
            "location": updated_location.strip(),
            "latitude": updated_latitude.strip(),
            "longitude": updated_longitude.strip(),
            "website": updated_website.strip(),
            "special_notes": updated_special_notes.strip()
        }}
    )
    flash(f"Cinema '{name}' updated successfully!", "success")
    return redirect(url_for('cinema.manage_cinemas'))


@cinema_bp.route('/manage_screenings', methods=['GET', 'POST'])
def manage_screenings():
    if request.method == 'POST':
        # Extract form data
        movie_title = request.form.get('movie_title')
        cinema_name = request.form.get('cinema_name')
        screening_datetime = request.form.get('screening_datetime')  # Single datetime
        screening_format = request.form.get('screening_format')
        ticket_link = request.form.get('ticket_link')
        special_notes = request.form.get('special_notes')
        status = request.form.get('status')

        # Validation
        if not (movie_title and cinema_name and screening_datetime and screening_format and status):
            flash("All required fields must be filled out.", "danger")
            return redirect(url_for('cinema.manage_screenings'))

        # Insert / update screening
        screenings_collection.update_one(
            {"movie_title": movie_title, "cinema_name": cinema_name},
            {"$set": {
                "screening_datetime": screening_datetime,
                "screening_format": screening_format,
                "ticket_link": ticket_link,
                "special_notes": special_notes,
                "status": status,
            }},
            upsert=True
        )
        flash(f"Screening for '{movie_title}' at '{cinema_name}' added/updated successfully.", "success")
        return redirect(url_for('cinema.manage_screenings'))

    # GET request: Fetch all screenings, movie titles, and cinema names
    screenings = list(screenings_collection.find({}, {"_id": 0}))
    movies = list(movies_collection.find({}, {"_id": 0, "title": 1}))  # Fetch movie titles
    cinemas = list(cinemas_collection.find({}, {"_id": 0, "name": 1}))  # Fetch cinema names

    # Format screening_datetime for display
    for screening in screenings:
        if "screening_datetime" in screening and screening["screening_datetime"]:
            screening["screening_datetime"] = datetime.strptime(
                screening["screening_datetime"], '%Y-%m-%dT%H:%M'
            ).strftime('%Y-%m-%d %H:%M')

    return render_template('admin/manage_screenings.html', screenings=screenings, movies=movies, cinemas=cinemas)


# Add Screening 
@cinema_bp.route('/add_screening', methods=['POST'])
def add_screening():
    # Add a new screening to the db.
    movie_title = request.form.get('movie_title')
    cinema_name = request.form.get('cinema_name')
    screening_datetime = request.form.get('screening_datetime')  # Single datetime
    screening_format = request.form.get('screening_format')
    status = request.form.get('status')
    ticket_link = request.form.get('ticket_link')
    special_notes = request.form.get('special_notes')

    if not (movie_title and cinema_name and screening_datetime and screening_format and status):
        flash("All required fields (Movie, Cinema, Datetime, Format, Status) must be filled.", "danger")
        return redirect(url_for('cinema.manage_screenings'))

    # Prepare the new screening entry
    new_screening = {
        "movie_title": movie_title.strip(),
        "cinema_name": cinema_name.strip(),
        "screening_datetime": screening_datetime.strip(),  # Expecting a single date-time string
        "screening_format": screening_format.strip(),
        "status": status.strip(),
        "ticket_link": ticket_link.strip() if ticket_link else None,
        "special_notes": special_notes.strip() if special_notes else None
    }
    screenings_collection.insert_one(new_screening)
    flash(f"Screening for '{movie_title}' at '{cinema_name}' added successfully!", "success")
    return redirect(url_for('cinema.manage_screenings'))

# Update Screening
@cinema_bp.route('/update_screening/<movie_title>/<cinema_name>', methods=['POST'])
def update_screening(movie_title, cinema_name):
    # Update screening showtimes for movie and cinema.
    updated_datetime = request.form.get('screening_datetime')  # Updated datetime
    updated_format = request.form.get('screening_format')
    updated_status = request.form.get('status')
    updated_ticket_link = request.form.get('ticket_link')
    updated_notes = request.form.get('special_notes')

    # Dynamically build the update query with only non-empty fields
    update_fields = {}
    if updated_datetime:
        update_fields["screening_datetime"] = updated_datetime.strip()
    if updated_format:
        update_fields["screening_format"] = updated_format.strip()
    if updated_status:
        update_fields["status"] = updated_status.strip()
    if updated_ticket_link:
        update_fields["ticket_link"] = updated_ticket_link.strip()
    if updated_notes:
        update_fields["special_notes"] = updated_notes.strip()

    # Ensure there are fields to update
    if not update_fields:
        flash("No fields were provided for update.", "warning")
        return redirect(url_for('cinema.manage_screenings'))

    screenings_collection.update_one(
        {"movie_title": movie_title, "cinema_name": cinema_name},
        {"$set": update_fields}
    )
    flash(f"Showtimes for '{movie_title}' updated successfully!", "success")
    return redirect(url_for('cinema.manage_screenings'))

# Delete Screening
@cinema_bp.route('/delete_screening/<movie_title>/<cinema_name>', methods=['POST'])
def delete_screening(movie_title, cinema_name):
    # Delete a specific screening by movie title and cinema name.
    screenings_collection.delete_one({"movie_title": movie_title, "cinema_name": cinema_name})
    flash(f"Screening for '{movie_title}' at '{cinema_name}' deleted successfully!", "success")
    return redirect(url_for('cinema.manage_screenings'))


