from flask_wtf import FlaskForm

from wtforms import (
    StringField,
    TextAreaField,
    SubmitField
)

from wtforms.validators import (
    DataRequired,
    Optional
)


class ProductForm(FlaskForm):

    product_name = StringField(
        "Product Name",
        validators=[DataRequired()]
    )

    description = TextAreaField(
        "Description",
        validators=[Optional()]
    )

    submit = SubmitField(
        "Save Product"
    )