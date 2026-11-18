import re

from app.models.company import Company


class ValidationService:

    REQUIRED_COLUMNS = [
        "company_name",
        "general_email",
        "country",
    ]

    OPTIONAL_COLUMNS = [
        "products",
        "major_products",
        "other_products",
        "reignfarmx_match",
        "city",
        "website",
        "phone",
        "buyer_type",
        "source",
        "notes",
    ]

    @classmethod
    def validate(cls, dataframe):

        errors = []

        # ---------------------------------------------------------
        # Required base columns
        # ---------------------------------------------------------

        for column in cls.REQUIRED_COLUMNS:

            if column not in dataframe.columns:

                errors.append(
                    f"Missing column: {column}"
                )

        # ---------------------------------------------------------
        # Product column
        #
        # Accept either:
        # products
        # OR
        # major_products
        # ---------------------------------------------------------

        if (
            "products" not in dataframe.columns
            and "major_products" not in dataframe.columns
        ):

            errors.append(
                "Missing column: products or major_products"
            )

        if errors:

            return {
                "success": False,
                "errors": errors
            }

        # ---------------------------------------------------------
        # Normalize product column
        # ---------------------------------------------------------

        if "products" not in dataframe.columns:

            dataframe["products"] = (
                dataframe["major_products"]
            )

        # ---------------------------------------------------------
        # Result
        # ---------------------------------------------------------

        result = {

            "success": True,

            "rows": [],

            "summary": {

                "total": 0,

                "valid": 0,

                "duplicates": 0,

                "invalid": 0

            }

        }

        # ---------------------------------------------------------
        # Validate rows
        # ---------------------------------------------------------

        for _, row in dataframe.iterrows():

            item = cls.validate_row(row)

            result["rows"].append(item)

            result["summary"]["total"] += 1

            if item["status"] == "Valid":

                result["summary"]["valid"] += 1

            elif item["status"] == "Duplicate":

                result["summary"]["duplicates"] += 1

            else:

                result["summary"]["invalid"] += 1

        return result

    @staticmethod
    def validate_row(row):

        company = str(
            row.get("company_name", "")
        ).strip()

        email = str(
            row.get("general_email", "")
        ).strip().lower()

        country = str(
            row.get("country", "")
        ).strip()

        product = str(
            row.get("products", "")
        ).strip()

        # ---------------------------------------------------------
        # Company validation
        # ---------------------------------------------------------

        if not company:

            return {
                "status": "Invalid",
                "company_name": company,
                "email": email,
                "country": country,
                "product": product,
                "reason": "Company name missing"
            }

        # ---------------------------------------------------------
        # Email validation
        # ---------------------------------------------------------

        if not email:

            return {
                "status": "Invalid",
                "company_name": company,
                "email": email,
                "country": country,
                "product": product,
                "reason": "Email missing"
            }

        regex = r"^[^@]+@[^@]+\.[^@]+$"

        if not re.match(regex, email):

            return {
                "status": "Invalid",
                "company_name": company,
                "email": email,
                "country": country,
                "product": product,
                "reason": "Invalid email"
            }

        # ---------------------------------------------------------
        # Product validation
        # ---------------------------------------------------------

        if not product:

            return {
                "status": "Invalid",
                "company_name": company,
                "email": email,
                "country": country,
                "product": product,
                "reason": "Product missing"
            }

        # ---------------------------------------------------------
        # Duplicate check
        # ---------------------------------------------------------

        exists = Company.query.filter_by(
            email=email
        ).first()

        if exists:

            return {
                "status": "Duplicate",
                "company_name": company,
                "email": email,
                "country": country,
                "product": product,
                "reason": "Already exists"
            }

        # ---------------------------------------------------------
        # Valid
        # ---------------------------------------------------------

        normalized_row = row.to_dict()

        # Make sure ImportService can always use products
        normalized_row["products"] = product

        # Make sure general_email is normalized
        normalized_row["general_email"] = email

        return {

            "status": "Valid",

            "company_name": company,

            "email": email,

            "country": country,

            "product": product,

            "reason": "",

            "row": normalized_row

        }