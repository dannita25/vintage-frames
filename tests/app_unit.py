# test_admin_routes.py
import pytest
from app import app  # Import the app instance
from flask import session

@pytest.fixture
def client():
    """
    Set up the Flask test client.
    """
    app.config['TESTING'] = True
    app.config['SECRET_KEY'] = 'test_secret_key'  # Mock secret key for session
    with app.test_client() as client:
        with app.app_context():
            yield client


def test_login_as_admin(client, mocker):
    """
    Test logging in as an admin and being redirected to the admin dashboard.
    """
    # Mock the database query to find the admin user
    mock_admin = {
        "username": "admin",
        "password": "hashed_admin_password",  # Use a pre-hashed password
        "role": "admin"
    }
    mocker.patch('app.users_collection.find_one', return_value=mock_admin)

    # Mock the password hashing check
    mocker.patch('werkzeug.security.check_password_hash', return_value=True)

    # Test the login page renders correctly
    response = client.get('/auth/login')
    assert response.status_code == 200
    assert b"Login" in response.data
    assert b"Don't have an account?" in response.data

    # Submit the login form with correct admin credentials
    response = client.post('/auth/login', data={
        "username": "admin",
        "password": "correct_password"
    }, follow_redirects=True)

    # Check if redirected to admin dashboard
    assert response.status_code == 200
    assert b"Admin Dashboard" in response.data  # Adjust based on your dashboard content


def test_login_invalid_credentials(client, mocker):
    """
    Test logging in with invalid credentials.
    """
    # Mock the database query to return None (user not found)
    mocker.patch('app.users_collection.find_one', return_value=None)

    # Attempt to log in with invalid credentials
    response = client.post('/auth/login', data={
        "username": "invalid_user",
        "password": "wrong_password"
    })

    # Check the login page is rendered with an error message
    assert response.status_code == 200
    assert b"Invalid username or password" in response.data


def test_login_missing_fields(client):
    """
    Test logging in with missing fields.
    """
    # Attempt to log in without filling in the username and password
    response = client.post('/auth/login', data={
        "username": "",
        "password": ""
    })

    # Check the login page is rendered with an error message
    assert response.status_code == 200
    assert b"Please provide both username and password" in response.data


def test_admin_dashboard(client, mocker):
    """
    Test the admin dashboard renders correctly with dynamic data.
    """
    # Mock database counts for users and reviews
    mock_users_count = 120
    mock_reviews_count = 45
    mocker.patch('app.users_collection.count_documents', return_value=mock_users_count)
    mocker.patch('app.reviews_collection.count_documents', return_value=mock_reviews_count)

    # Simulate admin login
    with client.session_transaction() as sess:
        sess['username'] = 'admin'
        sess['role'] = 'admin'

    # Make the GET request to the admin dashboard
    response = client.get('/admin/dashboard')
    assert response.status_code == 200

    # Check for static content
    assert b"Admin Dashboard" in response.data
    assert b"This is the Admin dashboard!" in response.data
    assert b"Manage Users" in response.data
    assert b"Manage Reviews" in response.data

    # Check for dynamic content: total users and reviews
    assert b"Total Users" in response.data
    assert str(mock_users_count).encode() in response.data  # Check if the count appears in the response
    assert b"Total Reviews" in response.data
    assert str(mock_reviews_count).encode() in response.data  # Check if the count appears in the response


def test_manage_users(client, mocker):
    """
    Test the manage users page displays user data correctly.
    """
    # Mock users data
    mock_users = [
        {
            "username": "user1",
            "email": "user1@example.com",
            "role": "user",
            "watchlist": ["Inception", "The Godfather"]
        },
        {
            "username": "admin",
            "email": "admin@example.com",
            "role": "admin",
            "watchlist": []
        }
    ]

    # Patch the database call to return mock users
    mocker.patch('app.users_collection.find', return_value=mock_users)

    # Simulate admin login
    with client.session_transaction() as sess:
        sess['username'] = 'admin'
        sess['role'] = 'admin'

    # Make the GET request to the manage users page
    response = client.get('/admin/manage_users')
    assert response.status_code == 200

    # Check for static content
    assert b"Manage Users" in response.data
    assert b"Dashboard" in response.data
    assert b"Manage Reviews" in response.data

    # Check for dynamic user data
    for user in mock_users:
        assert user['username'].encode() in response.data
        assert user['email'].encode() in response.data
        assert user['role'].encode() in response.data
        if user['watchlist']:
            for movie in user['watchlist']:
                assert movie.encode() in response.data
        else:
            assert b"<em>No movies in watchlist</em>" in response.data


def test_edit_user(client, mocker):
    """
    Test editing a user's details.
    """
    # Mock the database update method
    mock_update = mocker.patch('app.users_collection.update_one', return_value=None)

    # Simulate admin login
    with client.session_transaction() as sess:
        sess['username'] = 'admin'
        sess['role'] = 'admin'

    # Send a POST request to edit a user
    response = client.post('/admin/edit_user/testuser', data={
        "new_username": "updateduser",
        "email": "updated@example.com"
    })

    # Verify the response
    assert response.status_code == 302  # Expect a redirect after success
    assert response.headers["Location"].endswith("/admin/manage_users")  # Redirect to manage users

    # Verify that the database update was called with the correct arguments
    mock_update.assert_called_once_with(
        {"username": "testuser"},  # Filter for the original username
        {"$set": {"username": "updateduser", "email": "updated@example.com"}}  # Update data
    )


def test_delete_user(client, mocker):
    """
    Test deleting a user via the admin panel.
    """
    # Mock the database delete operation
    mock_delete = mocker.patch('app.users_collection.delete_one', return_value=None)

    # Simulate admin login
    with client.session_transaction() as sess:
        sess['username'] = 'admin'
        sess['role'] = 'admin'

    # Send POST request to delete the user
    response = client.post('/admin/delete_user/testuser', follow_redirects=True)

    # Assertions
    # Check the response status code
    assert response.status_code == 200  # Check for successful redirect response
    assert b"User 'testuser' has been deleted successfully!" in response.data  # Flash message confirmation

    # Ensure the database delete operation was called with correct arguments
    mock_delete.assert_called_once_with({"username": "testuser"})



def test_manage_reviews(client, mocker):
    """
    Test the manage reviews page displays reviews correctly.
    """
    # Mock reviews data
    mock_reviews = [
        {
            "movie_title": "Inception",
            "username": "user1",
            "review": "Amazing movie!",
            "rating": 5,
            "_id": "1"
        },
        {
            "movie_title": "The Godfather",
            "username": "user2",
            "review": "A classic masterpiece.",
            "rating": 4,
            "_id": "2"
        }
    ]

    # Patch the database call to return mock reviews
    mocker.patch('app.reviews_collection.find', return_value=mock_reviews)

    # Simulate admin login
    with client.session_transaction() as sess:
        sess['username'] = 'admin'
        sess['role'] = 'admin'

    # Make the GET request to the manage reviews page
    response = client.get('/admin/manage_reviews')
    assert response.status_code == 200

    # Check for static content
    assert b"Manage Reviews" in response.data
    assert b"Dashboard" in response.data
    assert b"Manage Users" in response.data

    # Check for dynamic content: reviews data
    for review in mock_reviews:
        assert review['movie_title'].encode() in response.data
        assert review['username'].encode() in response.data
        assert review['review'].encode() in response.data
        assert f"{review['rating']} ★".encode() in response.data



def test_delete_review(client, mocker):
    """
    Test deleting a review via the admin panel.
    """
    # Mock the database delete operation
    mock_delete = mocker.patch('app.reviews_collection.delete_one', return_value=None)

    # Simulate admin login
    with client.session_transaction() as sess:
        sess['username'] = 'admin'
        sess['role'] = 'admin'

    # Send POST request to delete the review
    response = client.post('/admin/delete_review/1', follow_redirects=True)

    # Assertions
    # Check the response status code and presence of the success message
    assert response.status_code == 200  # Success after following redirects
    assert b"Review deleted successfully." in response.data  # Flash message confirmation

    # Ensure the delete operation was called with the correct review ID
    mock_delete.assert_called_once_with({"_id": "1"})

