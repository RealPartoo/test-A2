from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, DecimalField, TextAreaField, SelectField
from wtforms.validators import DataRequired, Email, Length, NumberRange

class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired()])

class RegisterForm(FlaskForm):
    name = StringField("Name", validators=[DataRequired(), Length(max=120)])
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired(), Length(min=6)])

class ItemForm(FlaskForm):
    title = StringField("Title", validators=[DataRequired()])
    artist = StringField("Artist", validators=[DataRequired()])
    gallery = StringField("Gallery", validators=[DataRequired()])
    type = SelectField("Type", choices=[
        ("Oil Painting","Oil Painting"),
        ("Pastel Painting","Pastel Painting"),
        ("Watercolor Painting","Watercolor Painting"),
        ("Acrylic Painting","Acrylic Painting"),
        ("Digital Painting","Digital Painting"),
    ])
    genre = SelectField("Genre", choices=[
        ("Illustrative","Illustrative"),
        ("Portrait","Portrait"),
        ("Surrealism","Surrealism"),
        ("Graffiti","Graffiti"),
        ("Comic","Comic"),
        ("Folk Art","Folk Art"),
    ])
    size = StringField("Size", validators=[DataRequired()])
    pricePerMonth = DecimalField("Price / Month", validators=[DataRequired(), NumberRange(min=0)])
    description = TextAreaField("Description", validators=[DataRequired(), Length(max=1000)])
