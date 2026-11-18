from app.extensions import db
from app.models.base import BaseModel


class Campaign(BaseModel):

    __tablename__ = "campaigns"

    name = db.Column(
        db.String(150),
        nullable=False
    )

    template_id = db.Column(
        db.Integer,
        db.ForeignKey(
            "email_templates.id",
            ondelete="SET NULL"
        ),
        nullable=True
    )

    status = db.Column(
        db.String(20),
        default="Draft"
    )

    description = db.Column(
        db.Text
    )

    recipients = db.relationship(
        "CampaignRecipient",
        back_populates="campaign",
        cascade="all, delete-orphan",
        lazy="selectin"
    )

    email_logs = db.relationship(
        "EmailLog",
        back_populates="campaign",
        cascade="all, delete-orphan"
    )

    template = db.relationship(
        "EmailTemplate"
    )

    def __repr__(self):
        return self.name