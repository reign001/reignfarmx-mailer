from app.extensions import db
from app.models.base import BaseModel


class Product(BaseModel):

    __tablename__ = "products"

    product_name = db.Column(
        db.String(150),
        nullable=False,
        unique=True
    )

    description = db.Column(
        db.Text
    )

    company_products = db.relationship(
        "CompanyProduct",
        back_populates="product",
        cascade="all, delete-orphan",
        lazy="selectin"
    )

    def __repr__(self):
        return self.product_name