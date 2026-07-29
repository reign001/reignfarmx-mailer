from flask_wtf import FlaskForm

from wtforms import (
    StringField,
    TextAreaField,
    SubmitField
)

from wtforms.validators import DataRequired


class EmailTemplateForm(FlaskForm):

    template_name = StringField(
        "Template Name",
        validators=[DataRequired()]
    )

    subject = StringField(
        "Email Subject",
        validators=[DataRequired()]
    )

    body = TextAreaField(
        "Email Body",
        validators=[DataRequired()]
    )

    submit = SubmitField(
        "Save Template"
    )