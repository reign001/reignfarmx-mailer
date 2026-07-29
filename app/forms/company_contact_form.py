from flask_wtf import FlaskForm

from wtforms import (
    StringField,
    TextAreaField,
    SelectField,
    BooleanField,
    SubmitField
)

from wtforms.fields import EmailField

from wtforms.validators import (
    DataRequired,
    Email,
    Optional
)


class CompanyContactForm(FlaskForm):

    first_name = StringField(
        "First Name",
        validators=[Optional()]
    )

    last_name = StringField(
        "Last Name",
        validators=[Optional()]
    )

    job_title = StringField(
        "Job Title",
        validators=[Optional()]
    )

    department = SelectField(
        "Department",
        choices=[
            ("", "-- Select Department --"),
            ("Procurement", "Procurement"),
            ("Purchasing", "Purchasing"),
            ("Import", "Import"),
            ("Export", "Export"),
            ("Logistics", "Logistics"),
            ("Sales", "Sales"),
            ("Management", "Management"),
            ("Finance", "Finance"),
            ("Quality Assurance", "Quality Assurance"),
            ("Other", "Other"),
        ],
        validators=[Optional()]
    )

    contact_type = SelectField(
        "Contact Type",
        choices=[
            ("", "-- Select Contact Type --"),
            ("Buyer", "Buyer"),
            ("Procurement Manager", "Procurement Manager"),
            ("Import Manager", "Import Manager"),
            ("Purchasing Officer", "Purchasing Officer"),
            ("Managing Director", "Managing Director"),
            ("CEO", "CEO"),
            ("Owner", "Owner"),
            ("Sales", "Sales"),
            ("Other", "Other"),
        ],
        validators=[Optional()]
    )

    email = EmailField(
        "Email Address",
        validators=[
            DataRequired(),
            Email()
        ]
    )

    phone = StringField(
        "Phone Number",
        validators=[Optional()]
    )

    linkedin = StringField(
        "LinkedIn Profile",
        validators=[Optional()]
    )

    preferred_contact_method = SelectField(
        "Preferred Contact Method",
        choices=[
            ("Email", "Email"),
            ("Phone", "Phone"),
            ("WhatsApp", "WhatsApp"),
            ("LinkedIn", "LinkedIn")
        ]
    )

    decision_level = SelectField(
        "Decision Level",
        choices=[
            ("Decision Maker", "Decision Maker"),
            ("Influencer", "Influencer"),
            ("Gatekeeper", "Gatekeeper"),
            ("Technical", "Technical"),
            ("Finance", "Finance"),
            ("Unknown", "Unknown")
        ]
    )

    status = SelectField(
        "Status",
        choices=[
            ("Active", "Active"),
            ("Inactive", "Inactive"),
            ("Left Company", "Left Company")
        ]
    )

    is_primary = BooleanField(
        "Primary Contact"
    )

    receive_campaigns = BooleanField(
        "Receive Campaigns",
        default=True
    )

    marketing_allowed = BooleanField(
        "Marketing Consent",
        default=True
    )

    notes = TextAreaField(
        "Notes",
        validators=[Optional()]
    )

    submit = SubmitField(
        "Save Contact"
    )