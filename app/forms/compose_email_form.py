from flask_wtf import FlaskForm

from wtforms import (
    SelectField,
    StringField,
    TextAreaField,
    SubmitField
)

from wtforms.validators import DataRequired


class ComposeEmailForm(FlaskForm):

    company = SelectField(
        "Company",
        coerce=int,
        validators=[DataRequired()]
    )

    template = SelectField(
        "Email Template",
        coerce=int,
        validators=[DataRequired()]
    )

    subject = StringField(
        "Subject",
        validators=[DataRequired()]
    )

    body = TextAreaField(
        "Email Body",
        validators=[DataRequired()]
    )

    submit = SubmitField(
        "Send Email"
    )