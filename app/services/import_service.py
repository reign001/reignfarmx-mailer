from app.extensions import db
import traceback
from app.models.company import Company
from app.models.product import Product
from app.models.company_product import CompanyProduct
from app.models.company_contact import CompanyContact

from app.services.csv_service import CSVService
from app.services.validation_service import ValidationService


class ImportService:

    @staticmethod
    def preview(file):
        dataframe = CSVService.read(file)

        print("CSV columns:", dataframe.columns.tolist())
        print("CSV row count:", len(dataframe))
        print("First rows:")
        print(dataframe.head().to_dict(orient="records"))

        result = ValidationService.validate(dataframe)

        print("Validation result:", result)

        return result

    @classmethod
    def import_records(cls, preview):

        created = 0
        skipped = 0
        errors = []

        for index, item in enumerate(preview["rows"], start=1):

            # Skip rows that failed validation
            if item["status"] != "Valid":

                skipped += 1

                errors.append({
                    "row": index,
                    "company": item.get("company_name", "Unknown"),
                    "error": item.get("reason", "Validation failed")
                })

                continue

            try:

                row = item["row"]

                company = cls.save_company(row)

                cls.save_product(
                    company,
                    row
                )

                cls.save_contact(
                    company,
                    row
                )

                created += 1

            except Exception as e:

                db.session.rollback()

                skipped += 1

                error = {
                    "row": index,
                    "company": row.get("company_name"),
                    "email": row.get("general_email"),
                    "error": str(e),
                    "traceback": traceback.format_exc()
                }

                errors.append(error)

                print("=" * 80)
                print(f"ROW: {index}")
                print(f"COMPANY: {row.get('company_name')}")
                print(f"EMAIL: {row.get('general_email')}")
                print(f"ERROR: {e}")
                print(traceback.format_exc())
                print("=" * 80)

        db.session.commit()

        return {
            "created": created,
            "skipped": skipped,
            "errors": errors
        }

    @staticmethod
    def save_company(row):
        if not row.get("company_name"):
            raise ValueError("Company name is missing.")

        if not row.get("general_email"):
            raise ValueError("General email is missing.")

        company = Company(

            company_name=row.get("company_name"),

            email=row.get("general_email"),

            website=row.get("website"),

            phone=row.get("phone"),

            country=row.get("country"),

            city=row.get("city"),

            buyer_type=row.get(
                "buyer_type",
                "Importer"
            ),

            source=row.get("source"),

            notes=row.get("notes"),

            verification_status="Verified",

            priority_score=50
        )

        db.session.add(company)

        db.session.flush()

        return company

    @staticmethod
    def save_product(company, row):

        product_name = str(
            row.get("products", "")
        ).strip()

        if not product_name:
            raise ValueError("Product is missing.")

        product = Product.query.filter_by(

            product_name=product_name

        ).first()

        if not product:

            product = Product(

                product_name=product_name

            )

            db.session.add(product)

            db.session.flush()

        company_product = CompanyProduct(

            company_id=company.id,

            product_id=product.id

        )

        db.session.add(company_product)

    @staticmethod
    def save_contact(company, row):

        email = row.get("contact_email")

        if not email:

            return

        contact = CompanyContact(

            company_id=company.id,

            first_name=row.get("first_name"),

            last_name=row.get("last_name"),

            email=email,

            phone=row.get("phone"),

            job_title=row.get("job_title"),

            is_primary=True

        )

        db.session.add(contact)