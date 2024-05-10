from flask_wtf import FlaskForm
from wtforms import StringField, EmailField, PasswordField, SubmitField, SelectField, DateField
from wtforms.validators import DataRequired, Email, EqualTo, Length, Optional
from wtforms.widgets import TextArea

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