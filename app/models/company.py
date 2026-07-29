from app.extensions import db
from app.models.base import BaseModel


class Company(BaseModel):

    __tablename__ = "companies"

    company_name = db.Column(
        db.String(200),
        nullable=False
    )

    email = db.Column(
        db.String(200),
        unique=True,
        nullable=False
    )

    campaigns = db.relationship(
    "CampaignRecipient",
    back_populates="company",
    cascade="all, delete-orphan",
    lazy="selectin")

    website = db.Column(
        db.String(250)
    )

    country = db.Column(
        db.String(100)
    )

    state = db.Column(
        db.String(100)
    )

    city = db.Column(
        db.String(100)
    )

    company_products = db.relationship(
        "CompanyProduct",
        back_populates="company",
        cascade="all, delete-orphan",
        lazy="selectin"
    )

    status = db.Column(
        db.String(20),
        default="Active"
    )

    last_contacted = db.Column(
        db.DateTime,
        nullable=True
    )

    notes = db.Column(
        db.Text
    )

    industry = db.Column(
    db.String(150)
    )

    company_type = db.Column(
        db.String(100)
    )

    industry = db.Column(
    db.String(150)
    )

    company_type = db.Column(
        db.String(100)
    )

    destination_port = db.Column(
        db.String(150)
    )

    preferred_incoterm = db.Column(
        db.String(30)
    )

    verified = db.Column(
        db.Boolean,
        default=False
    )

    linkedin = db.Column(
    db.String(300))

    contacts = db.relationship(
    "CompanyContact",
    back_populates="company",
    cascade="all, delete-orphan",
    lazy="selectin"
)

    def __repr__(self):
        return f"<Company {self.company_name}>"