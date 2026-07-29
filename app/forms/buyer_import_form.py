from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired
from wtforms import SelectField, SubmitField
from wtforms.validators import DataRequired


class BuyerImportForm(FlaskForm):

    commodity = SelectField(
        "Commodity",
        validators=[DataRequired()],
        choices=[]
    )

    country = SelectField(
        "Country",
        validators=[DataRequired()],
        choices=[
            ("Germany", "Germany"),
            ("USA", "USA"),
            ("Netherlands", "Netherlands"),
            ("Poland", "Poland"),
            ("France", "France"),
            ("United Kingdom", "United Kingdom"),
            ("Spain", "Spain"),
            ("Italy", "Italy"),
            ("Canada", "Canada"),
            ("UAE", "UAE")
        ]
    )

    csv_file = FileField(
        "CSV File",
        validators=[FileRequired()]
    )

    submit = SubmitField("Import Buyers")