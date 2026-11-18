from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired
from wtforms import SubmitField


class ImportForm(FlaskForm):

    csv_file = FileField(
        "CSV File",
        validators=[FileRequired()]
    )

    submit = SubmitField(
        "Upload CSV"
    )