from app.extensions import db
from app.models.base import BaseModel


class EmailLog(BaseModel):

    __tablename__ = "email_logs"

    company_id = db.Column(
        db.Integer,
        db.ForeignKey("companies.id"),
        nullable=False
    )

    template_id = db.Column(
        db.Integer,
        db.ForeignKey("email_templates.id"),
        nullable=False
    )

    recipient = db.Column(
        db.String(255),
        nullable=False
    )

    subject = db.Column(
        db.String(255),
        nullable=False
    )

    body = db.Column(
        db.Text,
        nullable=False
    )

    status = db.Column(
        db.String(30),
        default="Pending"
    )

    campaign_id = db.Column(
    db.Integer,
    db.ForeignKey("campaigns.id"),
    nullable=False
)

    campaign = db.relationship(
        "Campaign",
        back_populates="email_logs"
    )

    sent_at = db.Column(
        db.DateTime
    )

    error_message = db.Column(
        db.Text
    )

    company = db.relationship("Company")

    template = db.relationship("EmailTemplate")