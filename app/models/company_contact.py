from app.extensions import db
from app.models.base import BaseModel


class CompanyContact(BaseModel):

    __tablename__ = "company_contacts"

    company_id = db.Column(
        db.Integer,
        db.ForeignKey("companies.id"),
        nullable=False
    )

    first_name = db.Column(
        db.String(100)
    )

    last_name = db.Column(
        db.String(100)
    )

    job_title = db.Column(
        db.String(150)
    )

    department = db.Column(
        db.String(100)
    )

    contact_type = db.Column(
        db.String(50)
    )

    email = db.Column(
        db.String(200),
        unique=True,
        nullable=False,
        index=True
    )

    phone = db.Column(
        db.String(50)
    )

    linkedin = db.Column(
        db.String(300)
    )

    preferred_contact_method = db.Column(
        db.String(50),
        default="Email"
    )

    decision_level = db.Column(
        db.String(50),
        default="Unknown"
    )

    is_primary = db.Column(
        db.Boolean,
        default=False
    )

    receive_campaigns = db.Column(
        db.Boolean,
        default=True
    )

    marketing_allowed = db.Column(
        db.Boolean,
        default=True,
        nullable=False
    )

    status = db.Column(
        db.String(30),
        default="Active"
    )

    last_contacted = db.Column(
        db.DateTime
    )

    notes = db.Column(
        db.Text
    )

    company = db.relationship(
        "Company",
        back_populates="contacts"
    )

    def __repr__(self):
        return (
            f"{self.first_name or ''} "
            f"{self.last_name or ''} "
            f"<{self.email}>"
        )