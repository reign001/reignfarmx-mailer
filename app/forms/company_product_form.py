from flask_wtf import FlaskForm

from wtforms import (
    SelectField,
    StringField,
    IntegerField,
    BooleanField,
    SubmitField
)

from wtforms.validators import Optional, DataRequired


class CompanyProductForm(FlaskForm):

    product = SelectField(
        "Commodity",
        coerce=int,
        validators=[DataRequired()]
    )

    category = StringField(
        "Category",
        validators=[Optional()]
    )

    priority = IntegerField(
        "Priority",
        default=1
    )

    is_primary = BooleanField(
        "Primary Commodity"
    )

    quantity = StringField(
        "Expected Quantity",
        validators=[Optional()]
    )

    quality_specification = StringField(
        "Quality Specification",
        validators=[Optional()]
    )

    packaging = StringField(
        "Packaging",
        validators=[Optional()]
    )

    destination_country = StringField(
        "Destination Country",
        validators=[Optional()]
    )

    destination_port = StringField(
        "Destination Port",
        validators=[Optional()]
    )

    incoterm = StringField(
        "Incoterm",
        validators=[Optional()]
    )

    target_delivery = StringField(
        "Target Delivery",
        validators=[Optional()]
    )

    submit = SubmitField(
        "Save Product"
    )