from flask import Flask, g, render_template, redirect, flash
from flask_wtf import FlaskForm
from wtforms import StringField, EmailField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Email, EqualTo, Length
import mysql.connector
from werkzeug.security import generate_password_hash, check_password_hash



# Flask app instance
app = Flask(__name__)
# Secret key for CSRF protection
app.config['SECRET_KEY'] = "secretkey1119"
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
    all_users = g.cursor.fetchall() # This is only for testing purposes, don't do this in a real application
    return render_template('users.html', all_users=all_users)

# User account / profile
@app.route('/profile')
def profile():
    return render_template('profile.html')

# Signup
@app.route('/signup', methods=['GET','POST'])
def signup():
    form = SignupForm()
    reg_successful = False
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
            reg_successful = False
            return render_template('signup.html', form=form, reg_successful=reg_successful)
        if not users_with_same_name is None:
            reg_successful = False
            flash("An existing account with this display name already exists. Please select a unique display name.")
            return render_template('signup.html', form=form, reg_successful=reg_successful)
        else:
            hashed_password = generate_password_hash(password)
            query = 'INSERT INTO user_accounts (display_name, email_address, hashed_password, signup_date) VALUES (%s, %s, %s, CURDATE())'
            g.cursor.execute(query, (display_name, email, hashed_password))
            g.db.commit()
            reg_successful = True
            flash("Account registered successfully. You may log in.")
            return redirect('/login')
    return render_template('signup.html', form=form, reg_successful=reg_successful)

# Login
@app.route('/login', methods=['GET','POST'])
def login():
    form = LoginForm()
    login_successful = False
    if form.validate_on_submit():
        display_name = form.display_name_f.data
        query = 'SELECT * FROM user_accounts WHERE display_name = %s'
        g.cursor.execute(query, (display_name,))
        user = g.cursor.fetchone()
        if not (user is not None and check_password_hash(user[3], form.password_f.data)):
            login_successful = False
            flash("Login failed. Please check your credentials.")
            return render_template('login.html', form=form, login_successful=login_successful)
        else:
            login_successful = True
            # TODO - Login logic stuff like cookies and session and what not
            flash("Login successful.")
            # Redirect to relevant page?
    return render_template('login.html', form=form, login_successful=login_successful)



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