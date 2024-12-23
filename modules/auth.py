# File to handle all authentication-related routes 
from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from database.init_db import get_db
from flask_mail import Message
from itsdangerous import URLSafeTimedSerializer
from flask import current_app
from modules.extensions import mail 

# Blueprint for authentication
auth_bp = Blueprint('auth', __name__, template_folder='templates')

# Initialize the database and collections
db = get_db()
users_collection = db['users']

# Route for user registration
@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        # Collect user details from the form
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        # Validation
        if password != confirm_password:
            return render_template('register.html', error='Passwords do not match')

        # Check if user already exists
        if users_collection.find_one({'email': email}):
            return render_template('register.html', error='User already exists')

        # Save the user to the database
        hashed_password = generate_password_hash(password)

        users_collection.insert_one({
            'username': username,
            'email': email,
            'password': hashed_password,
            'role': 'user',  # Default role is 'user'
            'watchlist': []  # Initialize watchlist
        })

        return redirect(url_for('auth.login'))  # Redirect to login page
    return render_template('register.html')


# Route for user login
@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Extract form from data
        username = request.form['username']
        password = request.form['password']

        if not username or not password:
            return render_template('login.html', error='Please provide both username and password')

        # Find user in database
        user = users_collection.find_one({'username': username})

        if user and check_password_hash(user['password'], password):
            # Start user session
            session['username'] = user['username']
            session['role'] = user.get('role', 'user')  # Assign 'user' role by default if missing
            flash('Login successful!', 'success')

            # Redirect based on role
            if session['role'] == 'admin':
                return redirect(url_for('admin.admin_dashboard'))  # Redirect admins to the dashboard
            else:
                return redirect(url_for('home'))  # Redirect regular users to the home page
        else:
            return render_template('login.html', error='Invalid username or password')

    return render_template('login.html')


# Route for user logout
@auth_bp.route('/logout')
def logout():
    session.clear()  # Clear the session
    flash("You have been logged out.", "success")
    
    # Check if the user is admin
    if session.get('role') == 'admin':
        return redirect(url_for('admin.admin_dashboard'))  # Redirect admins
    return redirect(url_for('home'))  # Redirect regular users


# Optional: Route for forgot password
@auth_bp.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        # Process form submission
        pass
        email = request.form['email']
        user = users_collection.find_one({'email': email})

        if not user:
            flash('Email not found.', 'danger')
            return redirect(url_for('auth.forgot_password'))

        # Generate a secure token
        serializer = URLSafeTimedSerializer(current_app.secret_key)
        token = serializer.dumps(email, salt='password-reset-salt')
        reset_url = url_for('auth.reset_password', token=token, _external=True)

        # Send the reset email
        send_reset_email(email, reset_url)
        flash('A password reset link has been sent to your email.', 'info')
    return render_template('forgot_password.html')

# Route to reset password
@auth_bp.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    serializer = URLSafeTimedSerializer(current_app.secret_key)

    try:
        email = serializer.loads(token, salt='password-reset-salt', max_age=3600)  # Token expires in 1h
    except Exception as e:
        flash('The password reset link is invalid or has expired.', 'danger')
        return redirect(url_for('auth.forgot_password'))

    if request.method == 'POST':
        new_password = request.form['password']
        confirm_password = request.form['confirm_password']

        if new_password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return redirect(url_for('auth.reset_password', token=token))

        hashed_password = generate_password_hash(new_password)
        users_collection.update_one({'email': email}, {'$set': {'password': hashed_password}})
        flash('Your password has been reset successfully.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('reset_password.html')


# Helper function to send reset email
def send_reset_email(to_email, reset_url):
    msg = Message(
        subject="Password Reset Request",
        sender="edinburghvintageframes@gmail.com",
        recipients=[to_email]
    )
    msg.body = f"Click the link to reset your password: {reset_url}"
    
    try:
        mail.send(msg)  # Ensure `mail` is the initialized Mail object
        print("Email sent successfully.")
    except Exception as e:
        print(f"Failed to send email: {e}")

# Edit function for admin
@auth_bp.route('/profile/edit', methods=['GET', 'POST'])
def edit_profile():
    user_email = session.get('username')
    if not user_email:
        return redirect(url_for('auth.login'))
    
    user = users_collection.find_one({'email': user_email})
    if not user:
        return "User not found", 404
    
    if request.method == 'POST':
        # Update details
        username = request.form['username']
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        if password and password != confirm_password:
            return render_template('edit_profile.html', user=user, error='Passwords do not match')

        update_data = {'username': username}
        if password:
            update_data['password'] = generate_password_hash(password)

        users_collection.update_one({'email': user_email}, {'$set': update_data})

        return redirect(url_for('auth.profile'))
    
    return render_template('edit_profile.html', user=user)

@auth_bp.route('/profile/delete', methods=['POST'])
def delete_account():
    user_email = session.get('username')
    if not user_email:
        return redirect(url_for('auth.login'))
    
    # Remove the user from the database
    users_collection.delete_one({'email': user_email})
    
    # Clear session and redirect to home
    session.pop('username', None)
    return redirect(url_for('home'))



