# imports
import mysql.connector
from credentials import credentials
from flask import Flask, Response, g, render_template, redirect, request, url_for, flash
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from forms import MessageForm, SignupForm, LoginForm, EditProfileForm, PasswordChangeForm, PostForm, EditPostForm, SearchForm, CommentForm, EditCommentForm
from queries import query
from datetime import datetime, timedelta


"""
TODOS that I may (or may not (depends on if I touch the project again (depends on how much time I got spare))) do
    - Add the ability for users to select pfps from their machine and upload them
    - Add the ability for users to add media to posts
    - Add the ability to reply on comments
    - Add the ability to endorse and condemn comments (may require a new table)
    - The navbar search can be improved by improving the searching queries
    - Implement sharing of posts through messages
    - Implement notifications
    - Implement communities
    - ...
    - Testing current stuff
"""

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
    g.cursor.execute(query['select_user_by_id'], (user_id,))
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
        g.cursor.execute(query['select_posts_join_users_filter_blockage_status_privacy'], (current_user.id, current_user.id))
    else:
        g.cursor.execute(query['select_posts_join_users_filter_status_privacy'])
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
                g.cursor.execute(query['select_posts_join_users_filter_blockage_status_privacy_search'], (current_user.id, current_user.id, '%'+search_query+'%', '%'+search_query+'%'))
                posts = g.cursor.fetchall()
                g.cursor.execute(query['select_users_filter_blockage_search'], (current_user.id, '%'+search_query+'%',))
                users = g.cursor.fetchall()
            else:
                g.cursor.execute(query['select_posts_join_users_filter_status_privacy_search'], ('%'+search_query+'%', '%'+search_query+'%'))
                posts = g.cursor.fetchall()
                g.cursor.execute(query['select_users_filter_search'], ('%'+search_query+'%',))
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
            g.cursor.execute(query['select_user_by_display_name'], (form.display_name_f.data,))
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
                g.cursor.execute(query['insert_user_signup'], (form.display_name_f.data, form.email_f.data, hashed_password))
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
            g.cursor.execute(query['select_user_by_display_name'], (form.display_name_f.data,))
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
        g.cursor.execute(query['select_user_by_id'], (current_user.id,))
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
        g.cursor.execute(query['select_user_age_by_id'], (current_user.id,))
        user_info["age"] = g.cursor.fetchone()[0]
        # Get the user's days until their account is permanently deleted
        if user_info["account_status"] == "Deleted":
            remaining_days = (user_info['deleted_date'] + timedelta(days=7) - datetime.now()).days
            user_info["days_until_deletion"] = remaining_days
        # Get the current logged in user's posts
        g.cursor.execute(query['select_user_posts_by_id_order_date'], (current_user.id,))
        user_info["posts"] = g.cursor.fetchall()
        # Get the current logged in user's follower count
        g.cursor.execute(query['select_user_follow_count_by_id'], (current_user.id,))
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
        g.cursor.execute(query['select_user_by_id'], (current_user.id,))
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
            g.cursor.execute(query['update_user_profile'], (
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
            g.cursor.execute(query['select_user_hashed_password_by_id'], (current_user.id,))
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
            g.cursor.execute(query['update_user_password'], (new_hashed_password, current_user.id))
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
        g.cursor.execute(query['soft_delete_user_by_id'], (current_user.id,))
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
        g.cursor.execute(query['recover_user_by_id'], (current_user.id,))
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
        g.cursor.execute(query['select_user_by_id'], (user_id,))
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
        g.cursor.execute(query['select_user_age_by_id'], (user_id,))
        user_info["age"] = g.cursor.fetchone()[0]
        # Get the user's posts
        g.cursor.execute(query['select_user_posts_by_id_order_date'], (user_id,))
        user_info["posts"] = g.cursor.fetchall()
        # Get the user's follower count
        g.cursor.execute(query['select_user_follow_count_by_id'], (user_id,))
        user_info["followers"] = g.cursor.fetchone()[0]
        # Check if the user is following the user whose profile is being viewed
        if current_user.is_authenticated:
            g.cursor.execute(query['select_follow_instance_by_ids'], (current_user.id, user_id))
            if g.cursor.fetchone():
                user_info["is_already_followed"] = True
            else:
                user_info["is_already_followed"] = False
        # Check if the user has blocked the user whose profile is being viewed and vice versa
        if current_user.is_authenticated:
            g.cursor.execute(query['select_blocked_instance_by_ids'], (current_user.id, user_id))
            if g.cursor.fetchone():
                user_info["is_blocked"] = True
            else:
                user_info["is_blocked"] = False
            g.cursor.execute(query['select_blocked_instance_by_ids'], (user_id, current_user.id))
            if g.cursor.fetchone():
                flash("You have been blocked by this user.")
                return redirect(request.referrer or url_for('index'))
        return render_template('profile_view.html', user=user_info)
    except Exception as e:
        print(e)
        flash("An error occurred while fetching the user's profile.", "error")
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
        g.cursor.execute(query['select_follow_instance_by_ids'], (follower_id, followed_id))
        # Don't let the user follow a user if they are already following them
        if g.cursor.fetchone():
            return Response(status=204)
        # Don't let the user follow a user if they are blocked
        g.cursor.execute(query['select_blocked_instance_by_ids'], (followed_id, follower_id))
        if g.cursor.fetchone():
            flash("You cannot follow this user.")
            return redirect(request.referrer or url_for('index'))
        # Follow the user
        else:
            g.cursor.execute(query['insert_follow_instance_by_ids'], (follower_id, followed_id))
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
        g.cursor.execute(query['select_follow_instance_by_ids'], (follower_id, followed_id))
        # Don't let the user unfollow a user if they are not following them
        if not g.cursor.fetchone():
            return Response(status=204)
        # Unfollow the user
        else:
            g.cursor.execute(query['delete_follow_instance_by_ids'], (follower_id, followed_id))
            g.db.commit()
            return redirect(request.referrer or url_for('index'))
    except Exception as e:
        print(e)
        flash("An error occurred while trying to unfollow the user.", "error")
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
        g.cursor.execute(query['select_blocked_instance_by_ids'], (current_user.id, user_id))
        if g.cursor.fetchone():
            flash("User is already blocked.")
            return redirect(request.referrer or url_for('index'))
        # Block the user
        g.cursor.execute(query['insert_block_instance_by_ids'], (current_user.id, user_id))
        # Unfollow the user
        g.cursor.execute(query['delete_follow_instance_by_ids'], (current_user.id, user_id))
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
        g.cursor.execute(query['select_blocked_instance_by_ids'], (current_user.id, user_id))
        if not g.cursor.fetchone():
            flash("User is not blocked.")
            return redirect(request.referrer or url_for('index'))
        # Unblock the user
        g.cursor.execute(query['delete_blocked_instance_by_ids'], (current_user.id, user_id))
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
            g.cursor.execute(query['insert_post'], (current_user.id, form.title_f.data, form.contents_f.data))
            g.db.commit()
            flash("Post created.")
            # Redirect to profile page
            return redirect(url_for('profile'))
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
        g.cursor.execute(query['select_post_by_id'], (post_id,))
        post = g.cursor.fetchone()
        if not post:
            flash("Post not found.")
            return redirect(url_for('index'))
        # Check if the owner has blocked the user or the user has blocked the owner
        if current_user.is_authenticated:
            g.cursor.execute(query['select_block_existence'], (post[1], current_user.id, current_user.id, post[1]))
            if g.cursor.fetchone():
                flash("You cannot view this post.")
                return redirect(request.referrer or url_for('index'))
        # Get the endorsement and condemnation count of the post
        g.cursor.execute(query['select_endorsement_count'], (post_id,))
        post_endorsements = g.cursor.fetchone()[0]
        g.cursor.execute(query['select_condemnation_count'], (post_id,))
        post_condemnations = g.cursor.fetchone()[0]
        # Check if the user has already endorsed or condemned the post
        if current_user.is_authenticated:
            g.cursor.execute(query['select_endorsement_by_post_user'], (current_user.id, post_id))
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
            g.cursor.execute(query['insert_comment'], (post_id, current_user.id, form.contents_f.data))
            g.db.commit()
            form.contents_f.data = ""
            flash("Comment posted.")
            return redirect(request.referrer or url_for('index'))
        # Get the comments on the post if any, whilst also checking blocking conditions
        if current_user.is_authenticated:
            g.cursor.execute(query['select_post_comments_filter_blockage_status_privacy'], (current_user.id, current_user.id, post_id))
        else:
            g.cursor.execute(query['select_post_comments_filter_status_privacy'], (post_id,))
        post_comments = g.cursor.fetchall()
        # Get the number of comments on the post
        g.cursor.execute(query['select_comment_count_on_post'], (post_id,))
        comment_count = g.cursor.fetchone()[0]
        # Get the privacy of the user who created the post and use that accordingly
        g.cursor.execute(query['select_user_by_id'], (post[1],))
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
        g.cursor.execute(query['select_post_by_id'], (post_id,))
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
            g.cursor.execute(query['update_post'], (form.title_f.data, form.contents_f.data, post_id))
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
        g.cursor.execute(query['select_post_by_id'], (post_id,))
        post = g.cursor.fetchone()
        # Check if the post exists and the user is authorized to delete it
        if not post:
            flash("Post not found.")
            return redirect(request.referrer or url_for('index'))
        if current_user.id != post[1]:
            flash("You are not authorized to delete this post.", "error")
            return redirect(request.referrer or url_for('index'))
        # Delete the post
        g.cursor.execute(query['delete_post_by_id'], (post_id,))
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
        g.cursor.execute(query['select_endorsement_by_post_user'], (current_user.id, post_id))
        endorsement = g.cursor.fetchone()
        # Update the endorsement type if it already exists and is different from the new endorsement type
        if endorsement and endorsement[3] != endorsement_type:
            g.cursor.execute(query['update_endorsement_type'], (endorsement_type, endorsement[0]))
        # Remove endorsement if already exists 
        elif endorsement and endorsement[3] == endorsement_type:
            g.cursor.execute(query['delete_endorsement_by_id'], (endorsement[0],))
        # Insert a new endorsement record if it doesn't exist
        elif not endorsement:
            g.cursor.execute(query['insert_endorsement'], (current_user.id, post_id, endorsement_type))
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
        g.cursor.execute(query['select_comment_by_id'], (comment_id,))
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
            g.cursor.execute(query['update_comment_content'], (form.contents_f.data, comment_id))
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
        g.cursor.execute(query['select_comment_by_id'], (comment_id,))
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
        g.cursor.execute(query['delete_comment_by_id'], (comment_id,))
        g.db.commit()
        flash("Comment deleted.")
        return redirect(request.referrer or url_for('index'))
    except Exception as e:
        print(e)
        flash("An error occurred while deleting the comment.", "error")
        return redirect(request.referrer or url_for('index'))
    
# Show all conversations of the current user
@app.route('/messages')
@login_required
def messages():
    try:
        # Fetch conversations for the current user
        g.cursor.execute(query['select_message_conversation_filter_blockage_status_order_date'], (current_user.id, current_user.id, current_user.id))
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
        g.cursor.execute(query['select_sender_receiver_status_privacy'], (sender_id, receiver_id))
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
        g.cursor.execute(query['select_blocked_instance_by_ids'], (receiver_id, sender_id))
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
        # Send the message
        if can_send_message(sender_id, receiver_id) == True:
            g.cursor.execute(query['insert_message'], (sender_id, receiver_id, content))
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
        g.cursor.execute(query['select_messages_of_users_order_date'], (current_user.id, receiver_id, receiver_id, current_user.id))
        messages = g.cursor.fetchall()
        # Fetch the display name and pfp of the receiver
        g.cursor.execute(query['select_user_by_id'], (receiver_id,))
        receiver = g.cursor.fetchone()
        # Send a message
        if form.validate_on_submit():
            send_message(current_user.id, receiver_id, form.contents_f.data)
            form.contents_f.data = ""
            return redirect(url_for('message_conversation', receiver_id=receiver_id))
        return render_template('message_conversation.html', messages=messages, form=form, receiver=receiver)
    except Exception as e:
        print(e)
        flash("An error occurred while fetching the conversation.", "error")
        return redirect(url_for('messages'))

# Admin, aka me hehe, routes (temporary routes maybe?)
# Shows all users
@app.route('/users')
@login_required
def users():
    try:
        if current_user.display_name != credentials['admin_display_name']:
            flash("You are not authorized to view all users.")
            return redirect(request.referrer or url_for('index'))
        g.cursor.execute(query['select_all_users'])
        all_users = g.cursor.fetchall()
        return render_template('users.html', all_users=all_users)
    except Exception as e:
        print(e)
        flash("An error occurred while fetching the users.", "error")
        return redirect(request.referrer or url_for('index'))

# Delete users
@app.route('/users/delete/<int:user_id>')
@login_required
def users_delete(user_id):
    try:
        if current_user.display_name != credentials['admin_display_name']:
            flash("You are not authorized to delete users.")
            return redirect(request.referrer or url_for('index'))
        g.cursor.execute(query['delete_user_by_id'], (user_id,))
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