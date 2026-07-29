from app.extensions import db
from app.models.base import BaseModel


class EmailTemplate(BaseModel):

    __tablename__ = "email_templates"

    template_name = db.Column(
        db.String(150),
        nullable=False,
        unique=True
    )

    subject = db.Column(
        db.String(255),
        nullable=False
    )

    body = db.Column(
        db.Text,
        nullable=False
    )

    active = db.Column(
        db.Boolean,
        default=True
    )

    def __repr__(self):
        return self.template_name