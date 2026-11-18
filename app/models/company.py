from app.extensions import db
from app.models.base import BaseModel


class Company(BaseModel):

    __tablename__ = "companies"

    company_name = db.Column(
        db.String(250),
        nullable=False
    )

    email = db.Column(
        db.String(254),
        unique=True,
        nullable=False
    )

    phone = db.Column(
    db.String(50))

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
    

    company_type = db.Column(
        db.String(100)
    )

    destination_port = db.Column(db.String(150))

    preferred_incoterm = db.Column(db.String(30))

    verified = db.Column(db.Boolean, default=False)

    linkedin = db.Column(db.String(300))

    contacts = db.relationship("CompanyContact", back_populates="company", cascade="all, delete-orphan", lazy="selectin")
    buyer_type = db.Column(db.String(200))
    website = db.Column(db.String(255))
    linkedin = db.Column(db.String(255))
    verification_status = db.Column(db.String(20), default="Verified")
    source = db.Column(db.Text)
    notes = db.Column(db.Text)
    priority_score = db.Column(db.Integer, default=50)
    def __repr__(self):
        return f"<Company {self.company_name}>"