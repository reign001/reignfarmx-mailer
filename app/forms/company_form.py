from flask_wtf import FlaskForm

from wtforms import (
    StringField,
    TextAreaField,
    SubmitField,
    SelectField
)

from wtforms.fields import EmailField

from wtforms.validators import (
    DataRequired,
    Email,
    Optional
)


class CompanyForm(FlaskForm):

    company_name = StringField(
        "Company Name",
        validators=[DataRequired()]
    )

    email = EmailField(
        "General Company Email",
        validators=[
            DataRequired(),
            Email()
        ]
    )

    website = StringField(
        "Website",
        validators=[Optional()]
    )

    country = StringField(
        "Country",
        validators=[DataRequired()]
    )

    state = StringField(
        "State",
        validators=[Optional()]
    )

    city = StringField(
        "City",
        validators=[Optional()]
    )

    status = SelectField(
        "Status",
        choices=[
            ("Active", "Active"),
            ("Inactive", "Inactive"),
            ("Prospect", "Prospect"),
            ("Customer", "Customer")
        ],
        validators=[DataRequired()]
    )

    notes = TextAreaField(
        "Notes",
        validators=[Optional()]
    )

    submit = SubmitField(
        "Save Company"
    )