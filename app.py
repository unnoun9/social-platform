from flask import Flask, g, render_template, redirect, request, url_for, flash
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import mysql.connector
from flask_wtf import FlaskForm
from wtforms import StringField, EmailField, PasswordField, SubmitField, SelectField, DateField
from wtforms.validators import DataRequired, Email, EqualTo, Length, Optional
from wtforms.widgets import TextArea



# Flask app instance
app = Flask(__name__)
# Secret key for CSRF protection
app.config['SECRET_KEY'] = "secretkey11199"



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

# Edit profile form class
class EditProfileForm(FlaskForm):
    display_name_f = StringField('Display name', validators=[DataRequired()])
    email_f = EmailField('Email', validators=[DataRequired()])
    pfp_url_f = StringField('Profile picture URL')
    about_f = StringField('About', widget=TextArea())
    gender_f = SelectField('Gender', choices=[('Male', 'Male'), ('Female', 'Female'), ('Other', 'Other')])
    date_of_birth_f = DateField('Date of Birth', validators=[Optional()])
    location_f = StringField('Location')
    privacy_f = SelectField('Account privacy', choices=[('Public', 'Public'), ('Private', 'Private')])
    # TODO - Change password field
    submit_f = SubmitField('Save changes')

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
        query = "SELECT id, display_name, email_address, hashed_password, signup_date, account_status, pfp_url, gender, about, location, date_of_birth, TIMESTAMPDIFF(YEAR, date_of_birth, CURDATE()) - (DATE_FORMAT(CURDATE(), '%m%d') < DATE_FORMAT(date_of_birth, '%m%d')) AS age, privacy FROM user_accounts WHERE id = %s"
        g.cursor.execute(query, (current_user.id,))
        user_details = g.cursor.fetchone()
        if not user_details:
            flash("User not found.", "error")
            return redirect(url_for('index'))
        user_info = {
            "display_name": user_details[1],
            "email_address": user_details[2],
            "signup_date": user_details[4],
            "account_status": user_details[5],
            "pfp_url": user_details[6],
            "gender": user_details[7],
            "about": user_details[8],
            "location": user_details[9],
            "date_of_birth": user_details[10],
            "age": user_details[11],
            "privacy": user_details[12]
        }
        return render_template('profile.html', user=user_info)
    except Exception as e:
        flash("An error occurred while fetching your profile data.", "error")
        app.logger.error(f"Error fetching user profile: {e}")
        return redirect(url_for('index'))
    
# Edit user profile
@app.route('/profile/edit', methods=['GET', 'POST'])
@login_required
def profile_edit():
    form = EditProfileForm()
    query = "SELECT id, display_name, email_address, hashed_password, signup_date, account_status, pfp_url, gender, about, location, date_of_birth, TIMESTAMPDIFF(YEAR, date_of_birth, CURDATE()) - (DATE_FORMAT(CURDATE(), '%m%d') < DATE_FORMAT(date_of_birth, '%m%d')) AS age, privacy FROM user_accounts WHERE id = %s"
    g.cursor.execute(query, (current_user.id,))
    user_details = g.cursor.fetchone()
    user_info = {
        "display_name": user_details[1],
        "email_address": user_details[2],
        "signup_date": user_details[4],
        "account_status": user_details[5],
        "pfp_url": user_details[6],
        "gender": user_details[7],
        "about": user_details[8],
        "location": user_details[9],
        "date_of_birth": user_details[10],
        "age": user_details[11],
        "privacy": user_details[12]
    }
    if request.method == 'GET':
        # Fetch existing data and populate the form only on GET request
        form.display_name_f.data = user_info["display_name"]
        form.email_f.data = user_info["email_address"]
        form.pfp_url_f.data = user_info["pfp_url"]
        form.about_f.data = user_info["about"]
        form.gender_f.data = user_info["gender"]
        form.date_of_birth_f.data = user_info["date_of_birth"]
        form.location_f.data = user_info["location"]
        form.privacy_f.data = user_info["privacy"]
        
    if form.validate_on_submit():
        # Update user details
        query = """
            UPDATE user_accounts SET
                display_name = %s,
                email_address = %s,
                pfp_url = %s,
                about = %s,
                gender = %s,
                date_of_birth = %s,
                location = %s,
                privacy = %s
            WHERE id = %s
        """
        g.cursor.execute(query, (
            form.display_name_f.data,
            form.email_f.data,
            form.pfp_url_f.data,
            form.about_f.data,
            form.gender_f.data,
            form.date_of_birth_f.data.strftime('%Y-%m-%d') if form.date_of_birth_f.data else None,
            form.location_f.data,
            form.privacy_f.data,
            current_user.id
        ))
        g.db.commit()
        flash('Profile updated successfully.')
        return redirect(url_for('profile'))
    return render_template('profile_edit.html', form=form, user=user_info)

# Third party view of user profiles / accounts
@app.route('/profile/user/<int:user_id>')
def profile_view(user_id):
    query = 'SELECT id, display_name, signup_date, account_status, pfp_url, gender, about, location, TIMESTAMPDIFF(YEAR, date_of_birth, CURDATE()) AS age, privacy FROM user_accounts WHERE id = %s'
    g.cursor.execute(query, (user_id,))
    user_details = g.cursor.fetchone()
    if not user_details:
        flash("User not found.", "error")
        return redirect(url_for('index'))
    user_info = {
            "display_name": user_details[1],
            "signup_date": user_details[2],
            "account_status": user_details[3],
            "pfp_url": user_details[4],
            "gender": user_details[5],
            "about": user_details[6],
            "location": user_details[7],
            "age": user_details[8],
            "privacy": user_details[9]
    }
    return render_template('profile_view.html', user=user_info)

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