from app.extensions import db
from app.models.base import BaseModel


class CompanyProduct(BaseModel):

    __tablename__ = "company_products"

    company_id = db.Column(
        db.Integer,
        db.ForeignKey("companies.id"),
        nullable=False
    )

    product_id = db.Column(
        db.Integer,
        db.ForeignKey("products.id"),
        nullable=False
    )

    priority = db.Column(
        db.Integer,
        default=1
    )

    category = db.Column(
        db.String(100)
    )

    is_primary = db.Column(
        db.Boolean,
        default=False
    )

    company = db.relationship(
        "Company",
        back_populates="company_products"
    )

    product = db.relationship(
        "Product",
        back_populates="company_products"
    )

    __table_args__ = (
        db.UniqueConstraint(
            "company_id",
            "product_id",
            name="uq_company_product"
        ),
    )

    def __repr__(self):
        return f"{self.company.company_name} - {self.product.product_name}"