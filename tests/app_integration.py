# test_integration.py
import pytest
from app import app  # Import the app instance from your app.py
from flask import session

@pytest.fixture
def client():
    """
    Set up the test client for the Flask app.
    """
    app.config['TESTING'] = True
    app.config['SECRET_KEY'] = 'test_secret_key'  # Mock secret key for session
    with app.test_client() as client:
        with app.app_context():
            yield client


def test_homepage(client):
    """
    Test that the homepage loads correctly and contains key content.
    """
    response = client.get('/')
    assert response.status_code == 200

    # Test for static content
    assert b"Welcome to Vintage Frames" in response.data
    assert b"Featured Films" in response.data
    assert b"Explore Local Spots" in response.data
    assert b"Personalized Recommendations" in response.data

    # Test for personalized recommendations message
    assert b"Are you already registered with us?" in response.data

    # Test dynamic content: Ensure the movies carousel is present
    assert b"filmCarousel" in response.data  # ID for the movie carousel



def test_admin_dashboard(client, mocker):
    """
    Test the admin dashboard renders correctly with dynamic data.
    """
    # Mock the database queries for users and reviews
    mocker.patch('app.users_collection.count_documents', return_value=100)  # Mock total users
    mocker.patch('app.reviews_collection.count_documents', return_value=50)  # Mock total reviews

    # Simulate admin login
    with client.session_transaction() as sess:
        sess['username'] = 'admin'
        sess['role'] = 'admin'

    # Make the GET request to the admin dashboard
    response = client.get('/admin/dashboard')
    assert response.status_code == 200

    # Check for static content
    assert b"Admin Dashboard" in response.data
    assert b"Manage Users" in response.data
    assert b"Manage Reviews" in response.data

    # Check for dynamic content
    assert b"Total Users" in response.data
    assert b"100" in response.data  # Mocked total user count
    assert b"Total Reviews" in response.data
    assert b"50" in response.data  # Mocked total review count



def test_watchlist_page(client, mocker):
    """
    Test the watchlist page renders correctly with and without movies.
    """
    # Mock the get_watchlist endpoint to return watchlist data
    mock_watchlist = [
        {"title": "Inception"},
        {"title": "The Godfather"}
    ]
    mocker.patch('app.movies_collection.find', return_value=mock_watchlist)

    # Simulate user login
    with client.session_transaction() as sess:
        sess['username'] = 'testuser'
        sess['role'] = 'user'

    # Test when the watchlist is not empty
    response = client.get('/get_watchlist')
    assert response.status_code == 200
    assert b"Inception" in response.data
    assert b"The Godfather" in response.data

    # Test rendering of the watchlist page
    response = client.get('/watchlist')
    assert response.status_code == 200
    assert b"My Watchlist" in response.data
    assert b"Inception" in response.data
    assert b"The Godfather" in response.data
    assert b"Your watchlist is currently empty" not in response.data  # Should not display empty state

    # Test when the watchlist is empty
    mocker.patch('app.movies_collection.find', return_value=[])
    response = client.get('/get_watchlist')
    assert response.status_code == 200
    assert b"[]" in response.data  # Empty list

    response = client.get('/watchlist')
    assert response.status_code == 200
    assert b"Your watchlist is currently empty" in response.data  # Empty state message should display



def test_local_spots_page(client, mocker):
    """
    Test the local vintage spots page renders correctly with data.
    """
    # Mock the local spots and cinemas data
    mock_spots = [
        {"name": "Vintage Shop", "description": "A great place for vintage items.", "location": "High Street", "latitude": 55.9533, "longitude": -3.1883},
        {"name": "Retro Cafe", "description": "Cozy cafe with retro vibes.", "location": "Main Road", "latitude": 55.9534, "longitude": -3.1890}
    ]
    mock_cinemas = [
        {"name": "Cinema 1", "latitude": 55.9531, "longitude": -3.1881},
        {"name": "Cinema 2", "latitude": 55.9532, "longitude": -3.1882}
    ]

    # Patch the database calls
    mocker.patch('app.local_spots_collection.find', return_value=mock_spots)
    mocker.patch('app.cinemas_collection.find', return_value=mock_cinemas)

    # Make a GET request to the local spots page
    response = client.get('/local_spots')
    assert response.status_code == 200

    # Check for static content
    assert b"Explore Local Vintage Spots" in response.data
    assert b"List of Vintage Spots" in response.data
    assert b"Map View" in response.data

    # Check for dynamic content: spot names and descriptions
    assert b"Vintage Shop" in response.data
    assert b"A great place for vintage items." in response.data
    assert b"Retro Cafe" in response.data
    assert b"Cozy cafe with retro vibes." in response.data

    # Check that cinemas data is included in the script for map markers
    assert b"Cinema 1" in response.data
    assert b"Cinema 2" in response.data



def test_user_profile_page(client, mocker):
    """
    Test the user profile page renders correctly with the user's data.
    """
    # Mock user data
    mock_user = {
        "username": "testuser",
        "email": "testuser@example.com"
    }

    # Patch the database call to return mock user data
    mocker.patch('app.users_collection.find_one', return_value=mock_user)

    # Simulate user login
    with client.session_transaction() as sess:
        sess['username'] = 'testuser'
        sess['role'] = 'user'

    # Test rendering the profile page
    response = client.get('/user_routes/profile')
    assert response.status_code == 200

    # Check for static content
    assert b"My Profile" in response.data
    assert b"Profile Overview" in response.data
    assert b"Account Settings" in response.data

    # Check for dynamic user data
    assert b"Username:" in response.data
    assert b"testuser" in response.data
    assert b"testuser@example.com" in response.data


def test_user_profile_update(client, mocker):
    """
    Test the account update functionality from the profile page.
    """
    # Mock user data
    mock_user = {
        "username": "testuser",
        "email": "testuser@example.com"
    }

    # Patch the database call to find the user
    mocker.patch('app.users_collection.find_one', return_value=mock_user)

    # Patch the database call to update the user
    mock_update = mocker.patch('app.users_collection.update_one')

    # Simulate user login
    with client.session_transaction() as sess:
        sess['username'] = 'testuser'
        sess['role'] = 'user'

    # Test updating the account
    response = client.post('/user_routes/profile/update', data={
        "username": "newuser",
        "email": "newuser@example.com",
        "password": "newpassword",
        "confirm_password": "newpassword"
    })

    # Check that the update endpoint redirects after success
    assert response.status_code == 302

    # Check that the database update was called with correct parameters
    mock_update.assert_called_once_with(
        {"username": "testuser"},
        {"$set": {
            "username": "newuser",
            "email": "newuser@example.com",
            "password": mocker.ANY  # Password is hashed, so we can't check its exact value
        }}
    )

def test_user_reviews_page(client, mocker):
    """
    Test the user reviews page renders correctly with and without reviews.
    """
    # Mock reviews for the user
    mock_reviews = [
        {
            "movie_title": "Inception",
            "review": "Amazing movie with a complex plot.",
            "created_at": "2024-12-23 14:00"
        },
        {
            "movie_title": "The Godfather",
            "review": "A masterpiece of cinema.",
            "created_at": "2024-12-20 10:30"
        }
    ]

    # Patch the database query for user reviews
    mocker.patch('app.reviews_collection.find', return_value=mock_reviews)

    # Simulate user login
    with client.session_transaction() as sess:
        sess['username'] = 'testuser'

    # Test rendering the reviews page with reviews
    response = client.get('/user_routes/my_reviews')
    assert response.status_code == 200

    # Check for static content
    assert b"My Reviews" in response.data

    # Check for dynamic content: reviews
    assert b"Inception" in response.data
    assert b"Amazing movie with a complex plot." in response.data
    assert b"The Godfather" in response.data
    assert b"A masterpiece of cinema." in response.data
    assert b"You haven't written any reviews yet." not in response.data  # Empty state should not appear

    # Test rendering the reviews page without reviews
    mocker.patch('app.reviews_collection.find', return_value=[])
    response = client.get('/user_routes/my_reviews')
    assert response.status_code == 200

    # Check for empty state message
    assert b"You haven't written any reviews yet." in response.data
    assert b"Inception" not in response.data
    assert b"The Godfather" not in response.data

