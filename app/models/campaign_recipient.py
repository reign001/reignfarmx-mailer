from app.extensions import db
from app.models.base import BaseModel


class CampaignRecipient(BaseModel):

    __tablename__ = "campaign_recipients"
    __table_args__ = (db.UniqueConstraint("campaign_id", "company_id", name="uq_campaign_recipient_company"),)

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

    # Current delivery state
    status = db.Column(
        db.String(30),
        default="Pending",
        nullable=False
    )

    # Sending
    sent_at = db.Column(
        db.DateTime
    )

    # Delivery
    delivered_at = db.Column(
        db.DateTime
    )

    # Opening
    opened_at = db.Column(
        db.DateTime
    )

    # Failure/bounce information
    error_message = db.Column(
        db.Text
    )

    # Number of times the tracking pixel was loaded
    open_count = db.Column(
        db.Integer,
        default=0,
        nullable=False
    )

    campaign = db.relationship(
        "Campaign",
        back_populates="recipients"
    )

    company = db.relationship(
        "Company",
        back_populates="campaigns"
    )

    recipient_email = db.Column(
    db.String(255))

    send_attempt = db.Column(
    db.Integer,
    default=1,
    nullable=False)

    # sent_to = db.Column(
    # db.String(255))
