# imports
import mysql.connector
from credentials import credentials
from flask import Flask, Response, g, render_template, redirect, request, url_for, flash
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from forms import MessageForm, SignupForm, LoginForm, EditProfileForm, PasswordChangeForm, PostForm, EditPostForm, SearchForm, CommentForm, EditCommentForm
from datetime import datetime, timedelta


# TODO - Make a different py file for all queries - Store them in a dictionary and call them as needed

# DONE - NEED TESTING - TODO - Add the ability to allow users to soft delete their account - their account will be permanently deleted after 7 days (maybe a procedure or a trigger for this? (dayyum))
# TODO - Add the ability for users to select pfps from their machine and upload them (hard)
# TODO - Add the ability for users to add media to posts (hard)
# TODO - Add the ability to reply on comments (hard)
# TODO - Add the ability to endorse and condemn comments (hard - may require a new table (yikes))
# TODO - The navbar search can be improved by improving the searching queries (hard and optional for now)

# DONE - NEED TESTING - TODO - Implement blocking users
# DONE - NEED TESTING - TODO - Implement messages
# TODO - Implement sharing of posts through messages
# TODO - Implement notifications
# TODO - Implement communities

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
    def __init__ (self, user_id, display_name, email_address, hashed_password, signup_date, account_status, pfp_url, about, location, date_of_birth, privacy, deleted_date):
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
        self.deleted_date = deleted_date

# Load user from database
@login_manager.user_loader
def load_user(user_id):
    query = 'SELECT * FROM user_accounts WHERE id = %s'
    g.cursor.execute(query, (user_id,))
    user = g.cursor.fetchone()
    if user:
        return User(user_id=user[0], display_name=user[1], email_address=user[2], hashed_password=user[3], signup_date=user[4], account_status=user[5], pfp_url=user[6], about=user[7], location=user[8], date_of_birth=user[9], privacy=user[10], deleted_date=user[11])
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
    # Get all posts and users for the feed
    if current_user.is_authenticated:
        query = """
            SELECT P.id, P.title, P.content, P.date_created,
            U.id, U.display_name, U.account_status, U.pfp_url, U.privacy
            FROM posts P
            JOIN user_accounts U ON P.user_id = U.id
            LEFT JOIN blocked_users B1 ON (B1.blocked_id = P.user_id AND B1.blocker_id = %s)
            LEFT JOIN blocked_users B2 ON (B2.blocked_id = %s AND B2.blocker_id = P.user_id)
            WHERE U.privacy = 'Public' AND U.account_status != 'Deleted'
            AND B1.blocked_id IS NULL
            AND B2.blocked_id IS NULL
            ORDER BY P.date_created DESC
        """
        g.cursor.execute(query, (current_user.id, current_user.id))
    else:
        query = """
            SELECT P.id, P.title, P.content, P.date_created,
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
@app.route('/search', methods=['GET', 'POST'])
def search():
    try:
        form = SearchForm()
        if form.validate_on_submit():
            search_query = form.searched_f.data.strip()
            # If the search field is empty, return a 204 status code
            if not search_query:
                return Response(status=204)
            # Search for posts and users that match the search query and pass them to the search page
            if current_user.is_authenticated:
                query = """
                    SELECT P.id, P.title, P.content, P.date_created,
                    U.id, U.display_name, U.account_status, U.pfp_url, U.privacy
                    FROM posts P
                    JOIN user_accounts U ON P.user_id = U.id
                    LEFT JOIN blocked_users B1 ON (B1.blocked_id = P.user_id AND B1.blocker_id = %s)
                    LEFT JOIN blocked_users B2 ON (B2.blocked_id = %s AND B2.blocker_id = P.user_id)
                    WHERE U.privacy = 'Public' AND U.account_status != 'Deleted' AND (P.title LIKE %s OR P.content LIKE %s)
                    AND B1.blocked_id IS NULL
                    AND B2.blocked_id IS NULL
                    ORDER BY P.date_created DESC
                """
                g.cursor.execute(query, (current_user.id, current_user.id, '%' + search_query + '%', '%' + search_query + '%'))
                posts = g.cursor.fetchall()
                query = """
                    SELECT *
                    FROM user_accounts U
                    LEFT JOIN blocked_users B ON (B.blocked_id = %s AND B.blocker_id = U.id)
                    WHERE display_name LIKE %s AND B.blocked_id IS NULL
                    ORDER BY display_name
                """
                g.cursor.execute(query, (current_user.id, '%' + search_query + '%',))
                users = g.cursor.fetchall()
            else:
                query = """
                    SELECT P.id, P.title, P.content, P.date_created,
                    U.id, U.display_name, U.account_status, U.pfp_url, U.privacy
                    FROM posts P
                    JOIN user_accounts U ON P.user_id = U.id
                    WHERE U.privacy = 'Public' AND account_status != 'Deleted' AND (P.title LIKE %s OR P.content LIKE %s)
                    ORDER BY P.date_created DESC
                """
                g.cursor.execute(query, ('%' + search_query + '%', '%' + search_query + '%'))
                posts = g.cursor.fetchall()
                query = """
                    SELECT *
                    FROM user_accounts
                    WHERE display_name LIKE %s
                    ORDER BY display_name
                """
                g.cursor.execute(query, ('%' + search_query + '%',))
                users = g.cursor.fetchall()
            return render_template('search.html', form=form, query=search_query, users=users, posts=posts)
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
                flash("Account registered. You may log in.")
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
                if user_obj.account_status == "Deleted":
                    flash("Warning: Your account is deleted or is scheduled to be deleted.")
                return redirect(request.referrer or url_for('profile'))
        return render_template('login.html', form=form)
    except Exception as e:
        print(e)
        flash("An error occurred while logging you in.", "error")
        return redirect(request.referrer or url_for('index'))

# Logout
@app.route('/logout')
@login_required
def logout():
    try:
        logout_user()
        flash("Logged out.")
        return redirect(url_for('index'))
    except Exception as e:
        print(e)
        flash("An error occurred while logging you out.", "error")
        return redirect(request.referrer or url_for('index'))

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
            flash("User not found.")
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
            "privacy": user_details[10],
            "deleted_date": user_details[11]
        }
        # Get the user's age
        query = """
            SELECT TIMESTAMPDIFF(YEAR, date_of_birth, CURDATE()) - (DATE_FORMAT(CURDATE(), '%m%d') < DATE_FORMAT(date_of_birth, '%m%d')) AS age
            FROM user_accounts
            WHERE id = %s
        """
        g.cursor.execute(query, (current_user.id,))
        user_info["age"] = g.cursor.fetchone()[0]
        # Get the user's days until their account is permanently deleted
        if user_info["account_status"] == "Deleted":
            remaining_days = (user_info['deleted_date'] + timedelta(days=7) - datetime.now()).days
            user_info["days_until_deletion"] = remaining_days
        # Get the current logged in user's posts
        query = """
            SELECT *
            FROM posts
            WHERE user_id = %s
            ORDER BY date_created DESC
        """
        g.cursor.execute(query, (current_user.id,))
        user_info["posts"] = g.cursor.fetchall()
        # Get the current logged in user's follower count
        query = """
            SELECT COUNT(*) FROM followers
            WHERE followed_id = %s
        """
        g.cursor.execute(query, (current_user.id,))
        user_info["followers"] = g.cursor.fetchone()[0]
        return render_template('profile.html', user=user_info)
    except Exception as e:
        print(e)
        flash("An error occurred while fetching your profile data.", "error")
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
        # Do not let the user edit their profile if their account is deleted
        if user_info['account_status'] == "Deleted":
            flash("Your account is already deleted or is scheduled to be deleted. You can't edit your profile.")
            return redirect(request.referrer or url_for('index'))
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
            flash('Profile updated.')
            return redirect(url_for('profile'))
        return render_template('profile_edit.html', form=form, user=user_info)
    except Exception as e:
        print(e)
        flash("An error occurred while updating your profile.", "error")
        return redirect(request.referrer or url_for('index'))

# Let a user change their password
@app.route('/profile/change_password', methods=['GET', 'POST'])
@login_required
def profile_password_change():
    try:
        form = PasswordChangeForm()
        if form.validate_on_submit():
            # Check if the old password is correct
            query = 'SELECT hashed_password FROM user_accounts WHERE id = %s'
            g.cursor.execute(query, (current_user.id,))
            hashed_password = g.cursor.fetchone()[0]
            if not check_password_hash(hashed_password, form.old_password_f.data):
                flash("Old password is incorrect. Please try again.")
                return render_template('profile_password_change.html', form=form)
            if form.old_password_f.data == form.new_password_f.data:
                flash("New password cannot be the same as the old password. Please try again.")
                return render_template('profile_password_change.html', form=form)
            # Check if the new password and confirm password fields match
            if form.new_password_f.data != form.new_password_confirm_f.data:
                flash("Passwords do not match. Please try again.")
                return render_template('profile_password_change.html', form=form)
            # Update the password
            new_hashed_password = generate_password_hash(form.new_password_f.data)
            query = 'UPDATE user_accounts SET hashed_password = %s WHERE id = %s'
            g.cursor.execute(query, (new_hashed_password, current_user.id))
            g.db.commit()
            flash("Password changed.")
            return redirect(url_for('profile'))
        return render_template('profile_password_change.html', form=form)
    except Exception as e:
        print(e)
        flash("An error occurred while changing the password.", "error")
        return redirect(request.referrer or url_for('index'))

# Let a user soft delete thier user account
@app.route('/profile/delete', methods=['GET', 'POST'])
@login_required
def profile_delete():
    try:
        if current_user.account_status == "Deleted":
            flash("Your account is already deleted or is scheduled to be deleted.")
            return redirect(request.referrer or url_for('index'))
        # Soft delete the account
        query = """
            UPDATE user_accounts
            SET account_status = 'Deleted', deleted_date = NOW()
            WHERE id = %s
        """
        g.cursor.execute(query, (current_user.id,))
        g.db.commit()
        flash("Account soft deleted. It will be permanently deleted after 7 days.")
    except Exception as e:
        flash("An error occurred while deleting the account.", "error")
        print(e)
    return redirect(url_for('index'))

# Let a user recover thier soft deleted account
@app.route('/profile/recover', methods=['GET', 'POST'])
@login_required
def profile_recover():
    try:
        if current_user.account_status != "Deleted":
            flash("Your account is not deleted.")
            return redirect(request.referrer or url_for('index'))
        # Recover the account
        query = """
            UPDATE user_accounts
            SET account_status = 'Active', deleted_date = NULL
            WHERE id = %s
        """
        g.cursor.execute(query, (current_user.id,))
        g.db.commit()
        flash("Account recovered.")
    except Exception as e:
        flash("An error occurred while recovering the account.", "error")
        print(e)
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
            flash("User not found.")
            return redirect(request.referrer or url_for('index'))
        user_info = {
            "id": user_id,
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
        # Get the user's follower count
        query = """
            SELECT COUNT(*) FROM followers
            WHERE followed_id = %s
        """
        g.cursor.execute(query, (user_id,))
        user_info["followers"] = g.cursor.fetchone()[0]
        # Check if the user is following the user whose profile is being viewed
        if current_user.is_authenticated:
            query = """
                SELECT * FROM followers
                WHERE follower_id = %s AND followed_id = %s
            """
            g.cursor.execute(query, (current_user.id, user_id))
            if g.cursor.fetchone():
                user_info["is_already_followed"] = True
            else:
                user_info["is_already_followed"] = False
        # Check if the user has blocked the user whose profile is being viewed and vice versa
        if current_user.is_authenticated:
            query = """
                SELECT 1 FROM blocked_users
                WHERE blocker_id = %s AND blocked_id = %s
            """
            g.cursor.execute(query, (current_user.id, user_id))
            if g.cursor.fetchone():
                user_info["is_blocked"] = True
            else:
                user_info["is_blocked"] = False
            query = """
                SELECT 1 FROM blocked_users
                WHERE blocker_id = %s AND blocked_id = %s
            """
            g.cursor.execute(query, (user_id, current_user.id))
            if g.cursor.fetchone():
                flash("You have been blocked by this user.")
                return redirect(request.referrer or url_for('index'))
        return render_template('profile_view.html', user=user_info)
    except Exception as e:
        print(e)
        flash("An error occurred while fetching the user's profile.", "error")
        return redirect(request.referrer or url_for('index'))

# Block a user
@app.route('/profile/user/block<int:user_id>')
@login_required
def block_user(user_id):
    try:
        # Do not let the user block a user if their account is deleted
        if current_user.account_status == "Deleted":
            flash("Your account is already deleted or is scheduled to be deleted. You can't block a user.")
            return redirect(request.referrer or url_for('index'))
        # Do not let the user block themselves
        if user_id == current_user.id:
            flash("You cannot block yourself.")
            return redirect(request.referrer or url_for('index'))
        # Check if the user is already blocked
        query = """
            SELECT * FROM blocked_users
            WHERE blocker_id = %s AND blocked_id = %s
        """
        g.cursor.execute(query, (current_user.id, user_id))
        if g.cursor.fetchone():
            flash("User is already blocked.")
            return redirect(request.referrer or url_for('index'))
        # Block the user
        query = """
            INSERT INTO blocked_users (blocker_id, blocked_id, date_blocked)
            VALUES (%s, %s, NOW())
        """
        g.cursor.execute(query, (current_user.id, user_id))
        # Unfollow the user
        query = """
            DELETE FROM followers
            WHERE follower_id = %s AND followed_id = %s
        """
        g.cursor.execute(query, (current_user.id, user_id))
        g.db.commit()
    except Exception as e:
        print(e)
        flash("An error occurred while blocking the user.", "error")
    return redirect(request.referrer or url_for('index'))
    
# Unblock a user
@app.route('/profile/user/unblock<int:user_id>')
@login_required
def unblock_user(user_id):
    try:
        # Do not let the user unblock a user if their account is deleted
        if current_user.account_status == "Deleted":
            flash("Your account is already deleted or is scheduled to be deleted. You can't unblock a user.")
            return redirect(request.referrer or url_for('index'))
        # Check if the user is already unblocked
        query = """
            SELECT * FROM blocked_users
            WHERE blocker_id = %s AND blocked_id = %s
        """
        g.cursor.execute(query, (current_user.id, user_id))
        if not g.cursor.fetchone():
            flash("User is not blocked.")
            return redirect(request.referrer or url_for('index'))
        # Unblock the user
        query = """
            DELETE FROM blocked_users
            WHERE blocker_id = %s AND blocked_id = %s
        """
        g.cursor.execute(query, (current_user.id, user_id))
        g.db.commit()
    except Exception as e:
        print(e)
        flash("An error occurred while unblocking the user.", "error")
    return redirect(request.referrer or url_for('index'))

# Create a post
@app.route('/post/create', methods=['GET','POST'])
@login_required
def post_create():
    try:
        # Do not let the user create a post if their account is deleted
        if current_user.account_status == "Deleted":
            flash("Your is already deleted or is scheduled to be deleted. You can't create a post.")
            return redirect(request.referrer or url_for('index'))
        form = PostForm()
        # Insert the post into the database, making sure that the authenticated user adds the post
        if form.validate_on_submit():
            query = """
                INSERT INTO POSTS (user_id, title, content, date_created)
                VALUES (%s, %s, %s, NOW())
            """
            g.cursor.execute(query, (current_user.id, form.title_f.data, form.contents_f.data))
            g.db.commit()
            flash("Post created.")
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

# View a post
@app.route('/post/<int:post_id>', methods=['GET', 'POST'])
def post_view(post_id):
    try:
        # Get the post details
        query = 'SELECT * FROM posts WHERE id = %s'
        g.cursor.execute(query, (post_id,))
        post = g.cursor.fetchone()
        if not post:
            flash("Post not found.")
            return redirect(url_for('index'))
        # Check if the owner has blocked the user or the user has blocked the owner
        if current_user.is_authenticated:
            query = """
                SELECT 1 FROM blocked_users
                WHERE (blocker_id = %s AND blocked_id = %s)
                OR (blocker_id = %s AND blocked_id = %s)
            """
            g.cursor.execute(query, (post[1], current_user.id, current_user.id, post[1]))
            if g.cursor.fetchone():
                flash("You cannot view this post.")
                return redirect(request.referrer or url_for('index'))
        # Get the endorsement and condemnation count of the post
        query = """
            SELECT COUNT(*) FROM endorsements
            WHERE post_id = %s AND endorsement_type = 'Endorsement'
        """
        g.cursor.execute(query, (post_id,))
        post_endorsements = g.cursor.fetchone()[0]
        query = """
            SELECT COUNT(*) FROM endorsements
            WHERE post_id = %s AND endorsement_type = 'Condemnation'
        """
        g.cursor.execute(query, (post_id,))
        post_condemnations = g.cursor.fetchone()[0]
        # Check if the user has already endorsed or condemned the post
        if current_user.is_authenticated:
            query = """
                SELECT * FROM endorsements
                WHERE user_id = %s AND post_id = %s
            """
            g.cursor.execute(query, (current_user.id, post_id))
            endorsement = g.cursor.fetchone()
            if endorsement:
                user_endorsement = endorsement[3]
            else:
                user_endorsement = None
        # The comment form
        form = CommentForm()
        # If form is submitted and the user is logged in, insert a new comment into the db
        if current_user.is_authenticated and form.validate_on_submit():
            # Do not let the user comment on a post if their account is deleted
            if current_user.account_status == "Deleted":
                flash("Your account is already deleted or is scheduled to be deleted. You can't comment on a post.")
                return redirect(request.referrer or url_for('index'))
            query = """
                INSERT INTO comments (post_id, user_id, content, date_created)
                VALUES (%s, %s, %s, NOW())
            """
            print(query) # the code never reaches here... why?
            g.cursor.execute(query, (post_id, current_user.id, form.contents_f.data))
            g.db.commit()
            form.contents_f.data = ""
            flash("Comment posted.")
            return redirect(request.referrer or url_for('index'))
        # Get the comments on the post if any, whilst also checking blocking conditions
        if current_user.is_authenticated:
            query = """
                SELECT C.id, C.content, C.date_created,
                U.id, U.display_name, U.account_status, U.pfp_url, U.privacy
                FROM comments C
                JOIN user_accounts U ON C.user_id = U.id
                LEFT JOIN blocked_users B1 ON (B1.blocked_id = C.user_id AND B1.blocker_id = %s)
                LEFT JOIN blocked_users B2 ON (B2.blocked_id = %s AND B2.blocker_id = C.user_id)
                WHERE C.post_id = %s AND U.account_status != 'Deleted'
                AND B1.blocked_id IS NULL
                AND B2.blocked_id IS NULL
                ORDER BY C.date_created DESC
            """
            g.cursor.execute(query, (current_user.id, current_user.id, post_id))
        else:
            query = """
                SELECT C.id, C.content, C.date_created,
                U.id, U.display_name, U.account_status, U.pfp_url, U.privacy
                FROM comments C
                JOIN user_accounts U ON C.user_id = U.id
                WHERE C.post_id = %s AND U.account_status != 'Deleted'
                ORDER BY C.date_created DESC
            """
            g.cursor.execute(query, (post_id,))
        post_comments = g.cursor.fetchall()
        # Get the number of comments on the post
        query = """
            SELECT COUNT(*) FROM comments
            WHERE post_id = %s
        """
        g.cursor.execute(query, (post_id,))
        comment_count = g.cursor.fetchone()[0]
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
        if current_user.is_authenticated:
            return render_template('post_view.html', post=post, user=user, post_endorsements=post_endorsements, post_condemnations=post_condemnations, user_endorsement=user_endorsement, form=form, post_comments=post_comments, comment_count=comment_count)
        else:
            return render_template('post_view.html', post=post, user=user, post_endorsements=post_endorsements, post_condemnations=post_condemnations, form=form, post_comments=post_comments, comment_count=comment_count)
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
            flash("Post not found.")
            return redirect(request.referrer or url_for('index'))
        if current_user.id != post[1]:
            flash("You are not authorized to edit this post.", "error")
            return redirect(request.referrer or url_for('index'))
        # Fetch existing data and populate the form only on GET request
        if request.method == 'GET':
            form.title_f.data = post[2]
            form.contents_f.data = post[3]
        # Update the post
        if form.validate_on_submit():
            query = """
                UPDATE posts
                SET title = %s, content = %s
                WHERE id = %s
            """
            g.cursor.execute(query, (form.title_f.data, form.contents_f.data, post_id))
            g.db.commit()
            flash("Post updated.")
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
            flash("Post not found.")
            return redirect(request.referrer or url_for('index'))
        if current_user.id != post[1]:
            flash("You are not authorized to delete this post.", "error")
            return redirect(request.referrer or url_for('index'))
        # Delete the post
        query = 'DELETE FROM posts WHERE id = %s'
        g.cursor.execute(query, (post_id,))
        g.db.commit()
        flash("Post deleted.")
        return redirect(request.referrer or url_for('index'))
    except Exception as e:
        print(e)
        flash("An error occurred while deleting the post.", "error")
        return redirect(request.referrer or url_for('index'))

# 'endorse' or 'condemn' a post
@app.route('/endorse/<int:post_id>/<string:endorsement_type>', methods=['GET', 'POST'])
@login_required
def endorse(post_id, endorsement_type):
    try:
        # Do not let the user endorse or condemn a post if their account is deleted
        if current_user.account_status == "Deleted":
            flash("Your account is already deleted or is scheduled to be deleted. You can't endorse or condemn a post.")
            return redirect(request.referrer or url_for('index'))
        # Check if endorsement_type is valid
        if endorsement_type not in ['Condemnation', 'Endorsement']:
            return redirect(request.referrer or url_for('index'))
        # Check if the user has already endorsed this post
        query = """
            SELECT * FROM endorsements
            WHERE user_id = %s AND post_id = %s
        """
        g.cursor.execute(query, (current_user.id, post_id))
        endorsement = g.cursor.fetchone()
        # Update the endorsement type if it already exists and is different from the new endorsement type
        if endorsement and endorsement[3] != endorsement_type:
            query = """
                UPDATE endorsements
                SET endorsement_type = %s, date_endorsed = NOW()
                WHERE id = %s
            """
            g.cursor.execute(query, (endorsement_type, endorsement[0]))
        # Remove endorsement if already exists 
        elif endorsement and endorsement[3] == endorsement_type:
            query = """
                DELETE FROM endorsements
                WHERE id = %s
            """
            g.cursor.execute(query, (endorsement[0],))
        # Insert a new endorsement record if it doesn't exist
        elif not endorsement:
            query = """
                INSERT INTO endorsements (user_id, post_id, endorsement_type, date_endorsed)
                VALUES (%s, %s, %s, NOW())
            """
            g.cursor.execute(query, (current_user.id, post_id, endorsement_type))
        g.db.commit()
        return redirect(request.referrer or url_for('index'))
    except Exception as e:
        g.db.rollback()
        print(e)
        flash("An error occurred while recording the endorsement.", "error")
        return redirect(request.referrer or url_for('index'))

# Edit comments
@app.route('/comment/edit/<int:comment_id>', methods=['GET','POST'])
@login_required
def comment_edit(comment_id):
    try:
        if not current_user.is_authenticated:
            flash('You must be logged in to edit your comment.')
            return redirect(request.referrer or url_for('index'))
        form = EditCommentForm()
        # Get the comment details
        query = """
            SELECT * FROM comments
            WHERE id = %s
        """
        g.cursor.execute(query, (comment_id,))
        comment = g.cursor.fetchone()
        # If there is no such comment, how can it be edited?
        if not comment:
            flash('Comment not found.')
            return redirect(request.referrer or url_for('index'))
        # Only allow the authorized user to edit thier own comment
        if current_user.id != comment[2]:
            flash('You are not authorized to edit this comment.')
            return redirect(request.referrer or url_for('index'))
        # Fetch existing data and populate the form only on GET request
        if request.method == 'GET':
            form.contents_f.data = comment[4]
        # Update the comment
        if form.validate_on_submit():
            query = """
                UPDATE comments
                SET content = %s
                WHERE id = %s
            """
            g.cursor.execute(query, (form.contents_f.data, comment_id))
            g.db.commit()
            flash("Comment updated.")
            return redirect(url_for('post_view', post_id=comment[1]))
        return render_template('comment_edit.html', form=form)
    except Exception as e:
        print(e)
        flash("An error occurred while editing the comment.", "error")
        return redirect(request.referrer or url_for('index'))

# Delete a comment
@app.route('/comment/delete/<int:comment_id>')
@login_required
def comment_delete(comment_id):
    try:
        if not current_user.is_authenticated:
            flash('You must be logged in to delete your comment.')
            return redirect(request.referrer or url_for('index'))
        # Get the comment details
        query = """
            SELECT * FROM comments
            WHERE id = %s
        """
        g.cursor.execute(query, (comment_id,))
        comment = g.cursor.fetchone()
        # If there is no such comment, how can it be edited?
        if not comment:
            flash('Comment not found.')
            return redirect(request.referrer or url_for('index'))
        # Only allow the authorized user to delete thier own comment
        if current_user.id != comment[2]:
            flash('You are not authorized to edit this comment.')
            return redirect(request.referrer or url_for('index'))
        # Delete the post
        query = 'DELETE FROM comments WHERE id = %s'
        g.cursor.execute(query, (comment_id,))
        g.db.commit()
        flash("Comment deleted.")
        return redirect(request.referrer or url_for('index'))
    except Exception as e:
        print(e)
        flash("An error occurred while deleting the comment.", "error")
        return redirect(request.referrer or url_for('index'))

# Allowing users to follow other users
@app.route('/follow/<int:followed_id>')
@login_required
def follow(followed_id):
    try:
        # Do not let the user follow a user if their account is deleted
        if current_user.account_status == "Deleted":
            flash("Your account is already deleted or is scheduled to be deleted. You can't follow a user.")
            return redirect(request.referrer or url_for('index'))
        follower_id = current_user.id
        # Don't allow the user to follow themselves lol
        if follower_id == followed_id:
            return Response(status=204)
        query = """
            SELECT * FROM followers
            WHERE follower_id = %s AND followed_id = %s
        """
        g.cursor.execute(query, (follower_id, followed_id))
        # Don't let the user follow a user if they are already following them
        if g.cursor.fetchone():
            return Response(status=204)
        # Don't let the user follow a user if they are blocked
        query = """
            SELECT 1 FROM blocked_users
            WHERE blocker_id = %s AND blocked_id = %s
        """
        g.cursor.execute(query, (followed_id, follower_id))
        if g.cursor.fetchone():
            flash("You cannot follow this user.")
            return redirect(request.referrer or url_for('index'))
        # Follow the user
        else:
            query = """
                INSERT INTO followers (follower_id, followed_id)
                VALUES (%s, %s)
            """
            g.cursor.execute(query, (follower_id, followed_id))
            g.db.commit()
            return redirect(request.referrer or url_for('index'))
    except Exception as e:
        print(e)
        flash("An error occurred while trying to follow the user.", "error")
        return redirect(request.referrer or url_for('index'))
    
# Allowing users to unfollow other users
@app.route('/unfollow/<int:followed_id>')
@login_required
def unfollow(followed_id):
    try:
        # Do not let the user unfollow a user if their account is deleted
        if current_user.account_status == "Deleted":
            flash("Your account is already deleted or is scheduled to be deleted. You can't unfollow a user.")
            return redirect(request.referrer or url_for('index'))
        follower_id = current_user.id
        # Don't allow the user to unfollow themselves lol
        if follower_id == followed_id:
            return Response(status=204)
        query = """
            SELECT * FROM followers
            WHERE follower_id = %s AND followed_id = %s
        """
        g.cursor.execute(query, (follower_id, followed_id))
        # Don't let the user unfollow a user if they are not following them
        if not g.cursor.fetchone():
            return Response(status=204)
        # Unfollow the user
        else:
            query = """
                DELETE FROM followers
                WHERE follower_id = %s AND followed_id = %s
            """
            g.cursor.execute(query, (follower_id, followed_id))
            g.db.commit()
            return redirect(request.referrer or url_for('index'))
    except Exception as e:
        print(e)
        flash("An error occurred while trying to unfollow the user.", "error")
        return redirect(request.referrer or url_for('index'))
    
# Show all conversations of the current user
@app.route('/messages')
@login_required
def messages():
    try:
        # Fetch conversations for the current user
        query = """
            SELECT U.id, U.display_name, U.pfp_url, MAX(M.date_sent) AS last_message_date
            FROM messages M
            JOIN user_accounts U ON (M.sender_id = U.id OR M.receiver_id = U.id)
            LEFT JOIN blocked_users B1 ON (M.sender_id = B1.blocker_id AND M.receiver_id = B1.blocked_id)
            LEFT JOIN blocked_users B2 ON (M.receiver_id = B2.blocker_id AND M.sender_id = B2.blocked_id)
            WHERE (M.sender_id = %s OR M.receiver_id = %s)
            AND U.id != %s
            AND B1.id IS NULL
            AND B2.id IS NULL
            GROUP BY U.id
            ORDER BY last_message_date DESC
        """
        g.cursor.execute(query, (current_user.id, current_user.id, current_user.id))
        conversations = g.cursor.fetchall()
        return render_template('messages.html', conversations=conversations)
    except Exception as e:
        print(e)
        flash("An error occurred while fetching messages.", "error")
        return redirect(request.referrer or url_for('index'))

# Helper function to check if the message can be sent or not
def can_send_message(sender_id, receiver_id):
    try:
        # Do not let the user message themselves
        if sender_id == receiver_id:
            flash("You cannot message yourself.")
            return False
        # Check the acount_status and privacy of both users
        query = """
            SELECT account_status, privacy
            FROM user_accounts
            WHERE id IN (%s, %s)
        """
        g.cursor.execute(query, (sender_id, receiver_id))
        statuses = g.cursor.fetchall()
        if not statuses or len(statuses) != 2:
            flash("User not found.")
            return False
        sender_status, receiver_status = statuses[0][0], statuses[1][0]
        sender_privacy, receiver_privacy = statuses[0][1], statuses[1][1]
        if sender_status == "Deleted" or receiver_status == "Deleted":
            flash("A deleted user cannot send or receive messages.")
            return False
        if sender_privacy == "Private" or receiver_privacy == "Private":
            flash("A private user cannot send or receive messages.")
            return False
        # Check if the receiver has blocked the sender
        query = """
            SELECT 1
            FROM blocked_users
            WHERE blocker_id = %s AND blocked_id = %s
        """
        g.cursor.execute(query, (receiver_id, sender_id))
        if g.cursor.fetchone():
            flash("You cannot message this user.")
            return False
        return True
    except Exception as e:
        print(e)
        flash("An error occurred while checking if the message can be sent.", "error")
        return False


# Helper function to send a message
def send_message(sender_id, receiver_id, content):
    try:
        if can_send_message(sender_id, receiver_id) == True:
            # Send the message
            query = """
                INSERT INTO messages (sender_id, receiver_id, content, date_sent)
                VALUES (%s, %s, %s, NOW())
            """
            g.cursor.execute(query, (sender_id, receiver_id, content))
            g.db.commit()
            flash('Message sent.')
    except Exception as e:
        print(e)
        flash("An error occurred while sending your message.", "error")

# Show a conversation between the current user and another user
@app.route('/messages/conversation/<int:receiver_id>', methods=['GET', 'POST'])
@login_required
def message_conversation(receiver_id):
    try:
        form = MessageForm()
        # Fetch the conversation between the current user and the specified user
        query = """
            SELECT M.id, M.sender_id, M.receiver_id, M.content, M.date_sent, U.display_name, U.pfp_url
            FROM messages M
            JOIN user_accounts U ON M.sender_id = U.id
            WHERE (M.sender_id = %s AND M.receiver_id = %s)
            OR (M.sender_id = %s AND M.receiver_id = %s)
            ORDER BY M.date_sent
        """
        g.cursor.execute(query, (current_user.id, receiver_id, receiver_id, current_user.id))
        messages = g.cursor.fetchall()
        # Fetch the display name and pfp of the receiver
        query = """
            SELECT id, display_name, pfp_url
            FROM user_accounts
            WHERE id = %s
        """
        g.cursor.execute(query, (receiver_id,))
        receiver_info = g.cursor.fetchone()
        # Send a message
        if form.validate_on_submit():
            send_message(current_user.id, receiver_id, form.contents_f.data)
            form.contents_f.data = ""
            return redirect(url_for('message_conversation', receiver_id=receiver_id))
        return render_template('message_conversation.html', messages=messages, form=form, receiver=receiver_info)
    except Exception as e:
        print(e)
        flash("An error occurred while fetching the conversation.", "error")
        return redirect(url_for('messages'))

# Admin routes (temporary routes maybe?)
# Shows all users
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

# Delete users
@app.route('/users/delete/<int:user_id>')
def users_delete(user_id):
    try:
        query = 'DELETE FROM user_accounts WHERE id = %s'
        g.cursor.execute(query, (user_id,))
        g.db.commit()
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