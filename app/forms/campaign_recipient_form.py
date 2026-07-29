from flask_wtf import FlaskForm
from wtforms import SelectMultipleField, SubmitField
from wtforms.validators import DataRequired


class CampaignRecipientForm(FlaskForm):

    companies = SelectMultipleField(
        "Companies",
        coerce=int,
        validators=[DataRequired()]
    )

    submit = SubmitField("Save Recipients")