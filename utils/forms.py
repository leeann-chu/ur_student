from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, DateField, SelectField, RadioField, TextAreaField, TimeField
from wtforms.validators import ValidationError, DataRequired, Email, EqualTo, Length, Optional
from datetime import date
from utils.models import User

class LoginForm(FlaskForm):
    username = StringField('Username or Email', [DataRequired()])
    password = PasswordField('Password', [DataRequired()])
    submit = SubmitField('Sign In')

class TwoFactorForm(FlaskForm):
    verification = StringField('Authentication Code')
    submit = SubmitField('Verify')

class RegistrationForm(FlaskForm):
    username = StringField('Username', [DataRequired()])
    email = StringField('Email', [DataRequired(), Email(message=('That\'s not a valid email address.')),
        Length(min=5, max=40)])
    password = PasswordField('Password', [DataRequired()])
    password2 = PasswordField('Repeat Password', [DataRequired(), EqualTo('password')])
    userType = RadioField("What are you?", choices=[('Student'), ('Teacher')],
                          validators=[DataRequired()])
    submit = SubmitField('Register')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user is not None:
            raise ValidationError('Please use a different username.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError('Please use a different email.')

class EditForm(FlaskForm):
    name = StringField('First and Last Name', [DataRequired(), Length(min=1, max=30)])
    dob = DateField('Birthdate', validators=[DataRequired(message="Please input birthday in mm/dd/yyyy format.")])
    email = StringField('Email',
        [Email(message=('That\'s not a valid email address.')),
        Length(min=5, max=40)])

    gradYear = SelectField('Gradutation Year', choices=[x for x in range(2000, 2030)], validators=[Optional()])
    pfp = StringField('Enter a link to your profile picture (For best results we recommend roughly 400x400)')

    def validate_dob(form, dob):
        if (dob.data > date.today()):
            raise ValidationError('Birthday must be before today.')

    def validate_name(form, name):
        try:
            name.data.split(" ")[1]
        except:
            raise ValidationError('Please include a first and last name.')

class CourseCreation(FlaskForm):
    numTitle = StringField('Course Number and Title', [DataRequired()])
    desc = TextAreaField('Enter your a quick description of your course')
    profName = StringField('Enter the professor\'s name')
    numCredits = StringField('Credits')
    roomNum = StringField('Room number')
    days = SelectField('Course schedule', choices=[(""), ("M/W"), ("T/Th"), ("F")])
    time = StringField('Course time')

class EditPassword(FlaskForm):
    oldPassword = PasswordField('Old Password', [DataRequired()])
    newPassword = PasswordField('New Password', [DataRequired()])
    submit = SubmitField('Change Password')

    def validate_newPassword(form, self):
        if self.data == form.oldPassword.data:
            raise ValidationError('New password cannot be the same as old password')

class ResetPasswordForm(FlaskForm):
    email = StringField('Email', [Optional(), Email(message=('That\'s not a valid email address.')),
        Length(min=5, max=40)])
    password = PasswordField('New Password')
    password2 = PasswordField('Repeat Password', [EqualTo('password')])
    submit = SubmitField('Reset Password')

class ClassesRegister(FlaskForm):
    submit = SubmitField('Register for Selected Classes')
