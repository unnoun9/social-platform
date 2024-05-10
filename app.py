from flask import Flask, g, render_template, redirect, url_for, flash
from flask_wtf import FlaskForm
from wtforms import StringField, EmailField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Email, EqualTo, Length
import mysql.connector
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user



# Flask app instance
app = Flask(__name__)
# Secret key for CSRF protection
app.config['SECRET_KEY'] = "secretkey11199"
# TODO - Cookies and Session stuff



# Database
# Initialize database at the start of every request
@app.before_request
def init_db():
    g.db = mysql.connector.connect(user='root', password='saa_social_dbProject_111', host='localhost', database='social', raise_on_warnings=True)
    g.cursor = g.db.cursor()

# Close database connection at the end of every request
@app.teardown_request
def teardown_db(exception):
    g.cursor.close()
    g.db.close()



# Initialize login manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# User class for login manager
class User(UserMixin):
    def __init__ (self, user_id, display_name, hashed_password):
        self.id = user_id
        self.display_name = display_name
        self.hashed_password = hashed_password

# Load user from database
@login_manager.user_loader
def load_user(user_id):
    query = 'SELECT id, display_name, hashed_password FROM user_accounts WHERE id = %s'
    g.cursor.execute(query, (user_id,))
    user = g.cursor.fetchone()
    if user:
        return User(user_id=user[0], display_name=user[1], hashed_password=user[2])
    return None



# Sign up form class
class SignupForm(FlaskForm):
    display_name_f = StringField('Display name', validators=[DataRequired()])
    email_f = EmailField('Email', validators=[DataRequired()])
    password_f = PasswordField('Password', validators=[DataRequired()])
    password_confirm_f = PasswordField('Confirm Password', validators=[DataRequired(), Length(min=8, max=80)])
    submit_f = SubmitField('Register')

# Login form class
class LoginForm(FlaskForm):
    display_name_f = StringField('Display name', validators=[DataRequired(), Length(min=3, max=50)])
    password_f = PasswordField('Password', validators=[DataRequired(), Length(min=8, max=80)])
    submit_f = SubmitField('Login')

# Post form class
class PostForm(FlaskForm):
    title_f = StringField('Title', validators=[DataRequired(), Length(min=3, max=100)])
    details_f = StringField('Details', validators=[DataRequired()])
    submit_f = SubmitField('Create post')



# Routes for different pages
# Index
@app.route('/')
def index():
    return render_template('index.html')

# Shows all users (for testing only)
@app.route('/users')
def users():
    query = 'SELECT * FROM user_accounts ORDER BY signup_date'
    g.cursor.execute(query)
    all_users = g.cursor.fetchall() # This is only for testing purposes
    return render_template('users.html', all_users=all_users)

# Signup
@app.route('/signup', methods=['GET','POST'])
def signup():
    form = SignupForm()
    if form.validate_on_submit():
        display_name = form.display_name_f.data
        email = form.email_f.data
        password = form.password_f.data
        password_confirm = form.password_confirm_f.data
        query = 'SELECT * FROM user_accounts WHERE display_name = %s'
        g.cursor.execute(query, (display_name,))
        users_with_same_name = g.cursor.fetchone()
        if password != password_confirm:
            flash("Passwords do not match. Please try again.")
            return render_template('signup.html', form=form)
        if not users_with_same_name is None:
            flash("An existing account with this display name already exists. Please select a unique display name.")
            return render_template('signup.html', form=form)
        else:
            hashed_password = generate_password_hash(password)
            query = 'INSERT INTO user_accounts (display_name, email_address, hashed_password, signup_date) VALUES (%s, %s, %s, CURDATE())'
            g.cursor.execute(query, (display_name, email, hashed_password))
            g.db.commit()
            flash("Account registered successfully. You may log in.")
            return redirect(url_for('login'))
    return render_template('signup.html', form=form)

# Login
@app.route('/login', methods=['GET','POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        display_name = form.display_name_f.data
        query = 'SELECT * FROM user_accounts WHERE display_name = %s'
        g.cursor.execute(query, (display_name,))
        user = g.cursor.fetchone()
        if not (user is not None and check_password_hash(user[3], form.password_f.data)):
            flash("Login failed. Please check your credentials.")
            return render_template('login.html', form=form)
        else:
            user_obj = load_user(user[0])
            login_user(user_obj)
            flash("Login successful.")
            return redirect(url_for('profile'))
    return render_template('login.html', form=form)

# Logout
@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash("Logged out successfully.")
    return redirect(url_for('index'))

# User account / profile
@app.route('/profile')
@login_required
def profile():
    try:
        query = 'SELECT display_name, pfp_url, about, gender, location, YEAR(CURDATE()) - YEAR(date_of_birth) AS age FROM user_accounts WHERE id = %s'
        g.cursor.execute(query, (current_user.id,))
        user_details = g.cursor.fetchone()
        if not user_details:
            flash("User not found.", "error")
            return redirect(url_for('index'))
        user_info = {
            "display_name": user_details[0],
            "pfp_url": user_details[1],
            "about": user_details[2],
            "gender": user_details[3],
            "location": user_details[4],
            "age": user_details[5],
        }
        return render_template('profile.html', user=user_info)
    except Exception as e:
        flash("An error occurred while fetching your profile data.", "error")
        app.logger.error(f"Error fetching user profile: {e}")
        return redirect(url_for('index'))

# Create posts
@app.route('/create_post', methods=['GET','POST'])
@login_required
def create_post():
    form = PostForm()
    post_successful = False
    if form.validate_on_submit():
        # TODO -  Create a post and store it in DB using the current logged in user's ID
        pass
    return '' # TODO - Return a the relevand page

# Error handlers
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def server_error(e):
    return render_template('500.html'), 500



# Run the app
if __name__ == '__main__':
    app.run(debug=True)