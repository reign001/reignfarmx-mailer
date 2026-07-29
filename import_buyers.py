import sys
from pathlib import Path

import pandas as pd

from app import create_app
from app.extensions import db

from app.models.company import Company
from app.models.product import Product
from app.models.company_product import CompanyProduct
from app.models.company_contact import CompanyContact


app = create_app()


# ============================================================
# STATISTICS
# ============================================================

stats = {
    "companies_created": 0,
    "companies_updated": 0,
    "products_created": 0,
    "products_linked": 0,
    "contacts_created": 0,
    "contacts_skipped": 0,
    "errors": 0,
}


# ============================================================
# PRODUCTS
# ============================================================

def get_or_create_product(product_name):

    product_name = str(product_name).strip()

    if not product_name:
        return None

    product = Product.query.filter_by(
        product_name=product_name
    ).first()

    if product:
        return product

    product = Product(
        product_name=product_name
    )

    db.session.add(product)
    db.session.flush()

    stats["products_created"] += 1

    print(f"Created Product : {product_name}")

    return product


# ============================================================
# COMPANY
# ============================================================

def get_or_create_company(row):

    website = str(row.get("website", "")).strip()
    email = str(row.get("general_email", "")).strip()
    name = str(row.get("company_name")).strip()

    company = None

    if website:
        company = Company.query.filter_by(
            website=website
        ).first()

    if not company and email:
        company = Company.query.filter_by(
            email=email
        ).first()

    if not company:
        company = Company.query.filter_by(
            company_name=name
        ).first()

    if company:

        company.website = website or company.website
        company.country = row.get("country")
        company.state = row.get("state")
        company.city = row.get("city")

        if hasattr(company, "industry"):
            company.industry = row.get("industry")

        if hasattr(company, "company_type"):
            company.company_type = row.get("company_type")

        if hasattr(company, "destination_port"):
            company.destination_port = row.get(
                "destination_port"
            )

        if hasattr(company, "preferred_incoterm"):
            company.preferred_incoterm = row.get(
                "preferred_incoterm"
            )

        company.notes = row.get("notes")

        stats["companies_updated"] += 1

        print(f"Updated Company : {company.company_name}")

        return company

    company = Company(

        company_name=name,

        email=email,

        website=website,

        country=row.get("country"),

        state=row.get("state"),

        city=row.get("city"),

        notes=row.get("notes")
    )

    if hasattr(company, "industry"):
        company.industry = row.get("industry")

    if hasattr(company, "company_type"):
        company.company_type = row.get("company_type")

    if hasattr(company, "destination_port"):
        company.destination_port = row.get(
            "destination_port"
        )

    if hasattr(company, "preferred_incoterm"):
        company.preferred_incoterm = row.get(
            "preferred_incoterm"
        )

    db.session.add(company)
    db.session.flush()

    stats["companies_created"] += 1

    print(f"Created Company : {company.company_name}")

    return company


# ============================================================
# CONTACTS
# ============================================================

def create_contact(company, email, contact_type):

    email = str(email).strip()

    if not email or email.lower() == "nan":
        return

    existing = CompanyContact.query.filter_by(
        email=email
    ).first()

    if existing:

        stats["contacts_skipped"] += 1

        return

    contact = CompanyContact(

        company_id=company.id,

        first_name=contact_type,

        email=email,

        contact_type=contact_type,

        is_primary=(contact_type == "General")
    )

    db.session.add(contact)

    stats["contacts_created"] += 1

    print(f"   Contact : {contact_type} -> {email}")


# ============================================================
# PRODUCTS
# ============================================================

def link_products(company, row):

    products = str(
        row.get("products", "")
    ).split("|")

    first = True

    for product_name in products:

        product_name = product_name.strip()

        if not product_name:
            continue

        product = get_or_create_product(
            product_name
        )

        if not product:
            continue

        exists = CompanyProduct.query.filter_by(

            company_id=company.id,

            product_id=product.id

        ).first()

        if exists:
            continue

        cp = CompanyProduct(

            company_id=company.id,

            product_id=product.id,

            is_primary=first

        )

        db.session.add(cp)

        stats["products_linked"] += 1

        first = False


# ============================================================
# IMPORT ONE CSV
# ============================================================

def import_csv(csv_file):

    print()

    print("=" * 70)

    print(f"IMPORTING : {csv_file}")

    print("=" * 70)

    df = pd.read_csv(csv_file)

    for _, row in df.iterrows():

        try:

            company = get_or_create_company(row)

            link_products(company, row)

            create_contact(
                company,
                row.get("general_email"),
                "General"
            )

            create_contact(
                company,
                row.get("procurement_email"),
                "Procurement"
            )

            create_contact(
                company,
                row.get("sales_email"),
                "Sales"
            )

            create_contact(
                company,
                row.get("ceo_email"),
                "CEO"
            )

        except Exception as e:

            stats["errors"] += 1

            print(e)

    db.session.commit()


# ============================================================
# MAIN
# ============================================================

def run(path):

    path = Path(path)

    if path.is_dir():

        files = sorted(
            path.glob("*.csv")
        )

        for csv in files:

            import_csv(csv)

    else:

        import_csv(path)

    print()

    print("=" * 70)

    print("IMPORT COMPLETE")

    print("=" * 70)

    print(f"Companies Created : {stats['companies_created']}")
    print(f"Companies Updated : {stats['companies_updated']}")
    print(f"Products Created  : {stats['products_created']}")
    print(f"Products Linked   : {stats['products_linked']}")
    print(f"Contacts Created  : {stats['contacts_created']}")
    print(f"Contacts Skipped  : {stats['contacts_skipped']}")
    print(f"Errors            : {stats['errors']}")

    print("=" * 70)


if __name__ == "__main__":

    if len(sys.argv) != 2:

        print()

        print("Usage:")

        print(
            "python import_buyers.py data/"
        )

        print(
            "or"
        )

        print(
            "python import_buyers.py data/hibiscus_buyers.csv"
        )

        sys.exit()

    with app.app_context():

        run(sys.argv[1])