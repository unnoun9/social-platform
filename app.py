# imports
import mysql.connector
from credentials import credentials
from flask import Flask, Response, g, render_template, redirect, request, url_for, flash
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from forms import SignupForm, LoginForm, EditProfileForm, PostForm, EditPostForm, SearchForm


# TODO - Make a different py file for all queries - Store them in a dictionary and call them as needed


# Flask app instance
app = Flask(__name__)
# Secret key for CSRF protection
app.config['SECRET_KEY'] = credentials["csrf_token"]

# Initialize database at the start of every request
@app.before_request
def init_db():
    g.db = mysql.connector.connect(user=credentials["db_user"], password=credentials["db_password"], host=credentials["db_host"], database=credentials["db_name"], raise_on_warnings=True)
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
    def __init__ (self, user_id, display_name, email_address, hashed_password, signup_date, account_status, pfp_url, about, location, date_of_birth, privacy):
        self.id = user_id
        self.display_name = display_name
        self.email_address = email_address
        self.hashed_password = hashed_password
        self.signup_date = signup_date
        self.account_status = account_status
        self.pfp_url = pfp_url
        self.about = about
        self.location = location
        self.date_of_birth = date_of_birth
        self.privacy = privacy

# Load user from database
@login_manager.user_loader
def load_user(user_id):
    query = 'SELECT * FROM user_accounts WHERE id = %s'
    g.cursor.execute(query, (user_id,))
    user = g.cursor.fetchone()
    if user:
        return User(user_id=user[0], display_name=user[1], email_address=user[2], hashed_password=user[3], signup_date=user[4], account_status=user[5], pfp_url=user[6], about=user[7], location=user[8], date_of_birth=user[9], privacy=user[10])
    return None




# Pass search form to the navbar
@app.context_processor
def pass_search_form():
    form = SearchForm()
    return dict(form=form)




# Routes
# Index
@app.route('/')
def index():
    # TODO - Fetch posts from all users and display them and shit
    query = """
        SELECT P.id, P.parent_id, P.title, P.content, P.date_created,
        U.id, U.display_name, U.account_status, U.pfp_url, U.privacy
        FROM posts P
        JOIN user_accounts U ON P.user_id = U.id
        WHERE U.privacy = 'Public' AND account_status != 'Deleted'
        ORDER BY P.date_created DESC
    """
    g.cursor.execute(query)
    posts_users = g.cursor.fetchall()
    return render_template('index.html', all_feed=posts_users)

# Search functionality (from the navbar)
@app.route('/search', methods=['POST'])
def search():
    try:
        form = SearchForm()
        if form.validate_on_submit():
            # If the search field is empty, return a 204 status code
            if not form.searched_f.data.strip():
                return Response(status=204)
            # Search for users and posts that match the search query and pass them to the search page
            # TODO - The SQL queris can be improved so that they reflect the search query better
            query = """
                SELECT *
                FROM user_accounts
                WHERE display_name LIKE %s
                ORDER BY display_name
            """
            g.cursor.execute(query, ('%' + form.searched_f.data + '%',))
            users = g.cursor.fetchall()
            query = """
                SELECT P.id, P.parent_id, P.title, P.content, P.date_created,
                U.id, U.display_name, U.account_status, U.pfp_url, U.privacy
                FROM posts P
                JOIN user_accounts U ON P.user_id = U.id
                WHERE U.privacy = 'Public' AND account_status != 'Deleted' AND (P.title LIKE %s OR P.content LIKE %s)
                ORDER BY P.date_created DESC
            """
            g.cursor.execute(query, ('%' + form.searched_f.data + '%', '%' + form.searched_f.data + '%'))
            posts = g.cursor.fetchall()
            return render_template('search.html', form=form, query=form.searched_f.data, users=users, posts=posts)
        # If the search field is empty, return a 204 status code
        if not form.searched_f.data.strip():
                return Response(status=204)
    except Exception as e:
        print(e)
        flash("An error occurred while searching.", "error")
        return redirect(request.referrer or url_for('index'))
    
# Signup
@app.route('/signup', methods=['GET','POST'])
def signup():
    try:
        # Do not let a logged in user to access signup route
        if current_user.is_authenticated:
            return redirect(url_for('profile'))
        form = SignupForm()
        if form.validate_on_submit():
            # Check if the user with the same display name exists or not
            query = 'SELECT * FROM user_accounts WHERE display_name = %s'
            g.cursor.execute(query, (form.display_name_f.data,))
            users_with_same_name = g.cursor.fetchone()
            if not users_with_same_name is None:
                flash("An existing account with this display name already exists. Please select a unique display name.")
                return render_template('signup.html', form=form)
            # Check if the password fields are equal
            if form.password_f.data != form.password_confirm_f.data:
                flash("Passwords do not match. Please try again.")
                return render_template('signup.html', form=form)
            # If everything is fine, register the user
            else:
                hashed_password = generate_password_hash(form.password_f.data)
                query = """
                    INSERT INTO user_accounts (display_name, email_address, hashed_password, signup_date)
                    VALUES (%s, %s, %s, NOW())
                """
                g.cursor.execute(query, (form.display_name_f.data, form.email_f.data, hashed_password))
                g.db.commit()
                flash("Account registered successfully. You may log in.")
                return redirect(url_for('login'))
    except Exception as e:
        print(e)
        flash("An error occurred while registering your account.", "error")
    return render_template('signup.html', form=form)

# Login
@app.route('/login', methods=['GET','POST'])
def login():
    try:
        # Do not let a logged in user to access login route
        if current_user.is_authenticated:
            return redirect(url_for('profile'))
        form = LoginForm()
        if form.validate_on_submit():
            # Check if the user exists and the password is correct
            query = 'SELECT * FROM user_accounts WHERE display_name = %s'
            g.cursor.execute(query, (form.display_name_f.data,))
            user = g.cursor.fetchone()
            if not (user is not None and check_password_hash(user[3], form.password_f.data)):
                flash("Login failed. Please check your credentials.")
                return render_template('login.html', form=form)
            # If everything is fine, log the user in
            else:
                user_obj = load_user(user[0])
                login_user(user_obj)
                flash("Login successful.")
                return redirect(url_for('profile'))
    except Exception as e:
        print(e)
        flash("An error occurred while logging you in.", "error")
    return render_template('login.html', form=form)

# Logout
@app.route('/logout')
@login_required
def logout():
    try:
        logout_user()
        flash("Logged out successfully.")
        return redirect(url_for('index'))
    except Exception as e:
        print(e)
        flash("An error occurred while logging you out.", "error")
        return redirect(url_for('profile'))

# User account / profile of the logged in user
@app.route('/profile')
@login_required
def profile():
    try:
        # Get the current logged in user's details
        query = 'SELECT * FROM user_accounts WHERE id = %s'
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
            "about": user_details[7],
            "location": user_details[8],
            "date_of_birth": user_details[9],
            "privacy": user_details[10]
        }
        # Get the user's age
        query = """
            SELECT TIMESTAMPDIFF(YEAR, date_of_birth, CURDATE()) - (DATE_FORMAT(CURDATE(), '%m%d') < DATE_FORMAT(date_of_birth, '%m%d')) AS age
            FROM user_accounts
            WHERE id = %s
        """
        g.cursor.execute(query, (current_user.id,))
        user_info["age"] = g.cursor.fetchone()[0]
        # Get the current logged in user's posts
        query = """
            SELECT *
            FROM posts
            WHERE user_id = %s
            ORDER BY date_created DESC
        """
        g.cursor.execute(query, (current_user.id,))
        user_info["posts"] = g.cursor.fetchall()
        return render_template('profile.html', user=user_info)
    except Exception as e:
        print(e)
        flash("An error occurred while fetching your profile data.", "error")
        # Return to the last visited page
        return redirect(request.referrer or url_for('index'))
    
# Edit user profile
@app.route('/profile/edit', methods=['GET', 'POST'])
@login_required
def profile_edit():
    try:
        form = EditProfileForm()
        query = 'SELECT * FROM user_accounts WHERE id = %s'
        g.cursor.execute(query, (current_user.id,))
        user_details = g.cursor.fetchone()
        user_info = {
            "display_name": user_details[1],
            "email_address": user_details[2],
            "signup_date": user_details[4],
            "account_status": user_details[5],
            "pfp_url": user_details[6],
            "about": user_details[7],
            "location": user_details[8],
            "date_of_birth": user_details[9],
            "privacy": user_details[10]
        }
        # Fetch existing data and populate the form only on GET request
        if request.method == 'GET':
            form.display_name_f.data = user_info["display_name"]
            form.email_f.data = user_info["email_address"]
            form.pfp_url_f.data = user_info["pfp_url"]
            form.about_f.data = user_info["about"]
            form.date_of_birth_f.data = user_info["date_of_birth"]
            form.location_f.data = user_info["location"]
            form.privacy_f.data = user_info["privacy"]
        # Update user details
        if form.validate_on_submit():
            query = """
                UPDATE user_accounts SET
                    display_name = %s,
                    email_address = %s,
                    pfp_url = %s,
                    about = %s,
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
                form.date_of_birth_f.data.strftime('%Y-%m-%d') if form.date_of_birth_f.data else None,
                form.location_f.data,
                form.privacy_f.data,
                current_user.id
            ))
            g.db.commit()
            flash('Profile updated successfully.')
            return redirect(url_for('profile'))
        return render_template('profile_edit.html', form=form, user=user_info)
    except Exception as e:
        print(e)
        flash("An error occurred while updating your profile.", "error")
        return redirect(request.referrer or url_for('index'))

# Third party view of user profiles
@app.route('/profile/user/<int:user_id>')
def profile_view(user_id):
    try:
        # Redirect the user to their own profile if they try to view their own profile
        if current_user.is_authenticated:
            if current_user.id == user_id:
                return redirect(url_for('profile'))
        # Get the user details
        query = 'SELECT * FROM user_accounts WHERE id = %s'
        g.cursor.execute(query, (user_id,))
        user_details = g.cursor.fetchone()
        if not user_details:
            flash("User not found.", "error")
            return redirect(request.referrer or url_for('index'))
        user_info = {
            "display_name": user_details[1],
            "email_address": user_details[2],
            "signup_date": user_details[4],
            "account_status": user_details[5],
            "pfp_url": user_details[6],
            "about": user_details[7],
            "location": user_details[8],
            "date_of_birth": user_details[9],
            "privacy": user_details[10]
        }
        # Get the user's age
        query = """
            SELECT TIMESTAMPDIFF(YEAR, date_of_birth, CURDATE()) - (DATE_FORMAT(CURDATE(), '%m%d') < DATE_FORMAT(date_of_birth, '%m%d')) AS age
            FROM user_accounts
            WHERE id = %s
        """
        g.cursor.execute(query, (user_id,))
        user_info["age"] = g.cursor.fetchone()[0]
        # Get the user's posts
        query = """
            SELECT *
            FROM posts
            WHERE user_id = %s
            ORDER BY date_created DESC
        """
        g.cursor.execute(query, (user_id,))
        user_info["posts"] = g.cursor.fetchall()
        return render_template('profile_view.html', user=user_info)
    except Exception as e:
        print(e)
        flash("An error occurred while fetching the user's profile.", "error")
        return redirect(request.referrer or url_for('index'))

# Delete a user account (soft delete - account_status = 'Deleted')
@app.route('/profile/delete/<int:user_id>')
@login_required
def profile_delete(user_id):
    # TODO - Add a confirmation dialog before deleting the account???
    pass 

# Create a post
@app.route('/post/create', methods=['GET','POST'])
@login_required
def post_create():
    try:
        form = PostForm()
        # Insert the post into the database, making sure that the authenticated user adds the post
        if form.validate_on_submit():
            query = """
                INSERT INTO POSTS (user_id, title, content, date_created)
                VALUES (%s, %s, %s, NOW())
            """
            g.cursor.execute(query, (current_user.id, form.title_f.data, form.contents_f.data))
            g.db.commit()
            flash("Post created successfully.")
            # Redirect to the newly created post
            query = """
                SELECT id
                FROM posts
                WHERE user_id = %s AND title = %s AND content = %s
            """
            g.cursor.execute(query, (current_user.id, form.title_f.data, form.contents_f.data))
            post_id = g.cursor.fetchone()
            return redirect(url_for('post_view', post_id=post_id[0]))
        return render_template('post_create.html', form=form)
    except Exception as e:
        print(e)
        flash("An error occurred while creating the post.", "error")
        return redirect(request.referrer or url_for('index'))

# Show a post
@app.route('/post/<int:post_id>')
def post_view(post_id):
    try:
        # Get the post details
        query = 'SELECT * FROM posts WHERE id = %s'
        g.cursor.execute(query, (post_id,))
        post = g.cursor.fetchone()
        if not post:
            flash("Post not found.", "error")
            return redirect(url_for('index'))
        # Get the privacy of the user who created the post and use that accordingly
        query = 'SELECT * FROM user_accounts WHERE id = %s'
        g.cursor.execute(query, (post[1],))
        user = g.cursor.fetchone()
        if user[10] == "Private":
            if current_user.is_authenticated:
                if current_user.id != post[1]:
                    flash("The owner of this post has a private account. You cannot view this post.")
                    return redirect(request.referrer or url_for('index'))
            else:
                flash("The owner of this post has a private account. You cannot view this post.")
                return redirect(request.referrer or url_for('index'))
        return render_template('post_view.html', post=post, user=user)
    except Exception as e:
        print(e)
        flash("An error occurred while fetching the post.", "error")
        return redirect(request.referrer or url_for('index'))

# Edit a post
@app.route('/post/edit/<int:post_id>', methods=['GET','POST'])
@login_required
def post_edit(post_id):
    try:
        form = EditPostForm()
        # Get the post details
        query = 'SELECT * FROM posts WHERE id = %s'
        g.cursor.execute(query, (post_id,))
        post = g.cursor.fetchone()
        # Check if the post exists and the user is authorized to edit it
        if not post:
            flash("Post not found.", "error")
            return redirect(request.referrer or url_for('index'))
        if current_user.id != post[1]:
            flash("You are not authorized to edit this post.", "error")
            return redirect(request.referrer or url_for('index'))
        # Fetch existing data and populate the form only on GET request
        if request.method == 'GET':
            form.title_f.data = post[3]
            form.contents_f.data = post[4]
        # Update the post
        if form.validate_on_submit():
            query = """
                UPDATE posts
                SET title = %s, content = %s
                WHERE id = %s
            """
            g.cursor.execute(query, (form.title_f.data, form.contents_f.data, post_id))
            g.db.commit()
            flash("Post updated successfully.")
            return redirect(url_for('post_view', post_id=post_id))
        return render_template('post_edit.html', form=form)
    except Exception as e:
        print(e)
        flash("An error occurred while editing the post.", "error")
        return redirect(request.referrer or url_for('index'))

# Delete a post
@app.route('/post/delete/<int:post_id>')
@login_required
def post_delete(post_id):
    try:
        # Get the post details
        query = 'SELECT * FROM posts WHERE id = %s'
        g.cursor.execute(query, (post_id,))
        post = g.cursor.fetchone()
        # Check if the post exists and the user is authorized to delete it
        if not post:
            flash("Post not found.", "error")
            return redirect(request.referrer or url_for('index'))
        if current_user.id != post[1]:
            flash("You are not authorized to delete this post.", "error")
            return redirect(request.referrer or url_for('index'))
        # Delete the post
        query = 'DELETE FROM posts WHERE id = %s'
        g.cursor.execute(query, (post_id,))
        g.db.commit()
        flash("Post deleted successfully.")
        return redirect(request.referrer or url_for('index'))
    except Exception as e:
        print(e)
        flash("An error occurred while deleting the post.", "error")
        return redirect(request.referrer or url_for('index'))

# Temporary route to shows all users (for testing purposes)
@app.route('/users')
def users():
    try:
        query = 'SELECT * FROM user_accounts ORDER BY signup_date'
        g.cursor.execute(query)
        all_users = g.cursor.fetchall() # This is only for testing purposes
        return render_template('users.html', all_users=all_users)
    except Exception as e:
        print(e)
        flash("An error occurred while fetching the users.", "error")
        return redirect(request.referrer or url_for('index'))

# Temporary route to delete users (for testing purposes)
@app.route('/users/delete/<int:user_id>')
def users_delete(user_id):
    try:
        query = 'DELETE FROM user_accounts WHERE id = %s'
        g.cursor.execute(query, (user_id,))
        g.db.commit()
        flash("User deleted successfully.")
    except Exception as e:
        print(e)
        flash("An error occurred while deleting the user.", "error")
    return redirect(url_for('users'))


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