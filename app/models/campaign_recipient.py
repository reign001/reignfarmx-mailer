from app.extensions import db
from app.models.base import BaseModel


class CampaignRecipient(BaseModel):

    __tablename__ = "campaign_recipients"

    campaign_id = db.Column(
        db.Integer,
        db.ForeignKey("campaigns.id"),
        nullable=False
    )

    company_id = db.Column(
        db.Integer,
        db.ForeignKey("companies.id"),
        nullable=False
    )

    status = db.Column(
        db.String(30),
        default="Pending"
    )

    sent_at = db.Column(
        db.DateTime
    )

    error_message = db.Column(
        db.Text
    )

    campaign = db.relationship(
        "Campaign",
        back_populates="recipients"
    )

    company = db.relationship(
        "Company",
        back_populates="campaigns"
    )