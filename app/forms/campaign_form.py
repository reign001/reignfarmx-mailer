from flask_wtf import FlaskForm

from wtforms import (
    StringField,
    TextAreaField,
    SelectField,
    SubmitField
)

from wtforms.validators import DataRequired


class CampaignForm(FlaskForm):

    campaign_name = StringField(
        "Campaign Name",
        validators=[DataRequired()]
    )

    description = TextAreaField(
        "Description"
    )

    template = SelectField(
        "Email Template",
        coerce=int,
        validators=[DataRequired()]
    )

    status = SelectField(
        "Status",
        choices=[
            ("Draft", "Draft"),
            ("Active", "Active"),
            ("Paused", "Paused"),
            ("Completed", "Completed")
        ],
        default="Draft"
    )

    submit = SubmitField(
        "Save Campaign"
    )