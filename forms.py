from flask_wtf import FlaskForm
from wtforms import StringField, EmailField, PasswordField, SubmitField, SelectField, DateField, TextAreaField
from wtforms.validators import DataRequired, Length, Optional
from wtforms.widgets import TextArea

# Sign up form class
class SignupForm(FlaskForm):
    display_name_f = StringField('Display name', validators=[DataRequired(), Length(min=2, max=50)])
    email_f = EmailField('Email', validators=[DataRequired()])
    password_f = PasswordField('Password', validators=[DataRequired()])
    password_confirm_f = PasswordField('Confirm Password', validators=[DataRequired(), Length(min=8, max=80)])
    submit_f = SubmitField('Register')

# Login form class
class LoginForm(FlaskForm):
    display_name_f = StringField('Display name', validators=[DataRequired(), Length(min=2, max=50)])
    password_f = PasswordField('Password', validators=[DataRequired(), Length(min=8, max=80)])
    submit_f = SubmitField('Login')

# Edit profile form class
class EditProfileForm(FlaskForm):
    display_name_f = StringField('Display name', validators=[DataRequired()])
    email_f = EmailField('Email', validators=[DataRequired()])
    pfp_url_f = StringField('Profile picture URL')
    about_f = TextAreaField('About', widget=TextArea(), validators=[Length(min=0, max=500)])
    date_of_birth_f = DateField('Date of Birth', validators=[Optional()])
    location_f = StringField('Location')
    privacy_f = SelectField('Account privacy', choices=[('Public', 'Public'), ('Private', 'Private')])
    # TODO - Password change field
    submit_f = SubmitField('Save changes')

# Post form class
class PostForm(FlaskForm):
    title_f = StringField('Title', validators=[DataRequired(), Length(min=1, max=100)])
    contents_f = TextAreaField('Details', widget=TextArea(), validators=[Length(min=0, max=10000)])
    submit_f = SubmitField('Create post')

# Post form class
class EditPostForm(FlaskForm):
    title_f = StringField('Title', validators=[DataRequired(), Length(min=1, max=100)])
    contents_f = TextAreaField('Details', widget=TextArea(), validators=[Length(min=0, max=10000)])
    submit_f = SubmitField('Save Changes')

# Seach form class
class SearchForm(FlaskForm):
    searched_f = StringField('Searched', validators=[DataRequired()])
    submit_f = SubmitField('Search')

# Comment form class
class CommentForm(FlaskForm):
    contents_f = TextAreaField('Comment', widget=TextArea(), validators=[DataRequired(), Length(min=1, max=1000)])
    submit_f = SubmitField('Comment')

# Comment form class
class EditCommentForm(FlaskForm):
    contents_f = TextAreaField('Comment', widget=TextArea(), validators=[DataRequired(), Length(min=1, max=1000)])
    submit_f = SubmitField('Save Changes')