from jinja2 import Template

from app.models.company_contact import CompanyContact


class TemplateService:

    @staticmethod
    def get_best_contact(company):

        if not company.contacts:
            return None

        # Primary contact
        for contact in company.contacts:
            if contact.is_primary:
                return contact

        # Procurement
        for contact in company.contacts:
            if contact.department and contact.department.lower() == "procurement":
                return contact

        # Purchasing
        for contact in company.contacts:
            if contact.department and contact.department.lower() == "purchasing":
                return contact

        # Sales
        for contact in company.contacts:
            if contact.department and contact.department.lower() == "sales":
                return contact

        return company.contacts[0]

    @staticmethod
    def render(company, template, contact=None):

        # ------------------------------------
        # Products
        # ------------------------------------

        company_products = company.company_products

        primary = next(
            (
                cp
                for cp in company_products
                if cp.is_primary
            ),
            None
        )

        if primary:

            primary_product = primary.product.product_name

        else:

            primary_product = ""

        # These fields are not currently stored
        # on CompanyProduct.
        quantity = ""

        packaging = ""

        destination_country = ""

        destination_port = ""

        incoterm = ""

        product_names = [
            cp.product.product_name
            for cp in company_products
        ]

        products = ", ".join(product_names)

        product_list = "\n".join(
            f"• {name}"
            for name in product_names
        )

        # ------------------------------------
        # Contact
        # ------------------------------------

        if contact:

            contact_name = (
                f"{contact.first_name} {contact.last_name or ''}"
            ).strip()

            first_name = contact.first_name or ""

            last_name = contact.last_name or ""

            job_title = contact.job_title or ""

            department = contact.department or ""

            contact_email = contact.email

        else:

            contact_name = "Procurement Team"

            first_name = ""

            last_name = ""

            job_title = ""

            department = ""

            contact_email = company.email

        # ------------------------------------
        # Context
        # ------------------------------------

        context = {

            "company_name": company.company_name,

            "website": company.website or "",

            "country": company.country or "",

            "city": company.city or "",

            "commodity": primary_product,

            "primary_product": primary_product,

            "products": products,

            "product_list": product_list,

            "quantity": quantity,

            "packaging": packaging,

            "destination_country": destination_country,

            "destination_port": destination_port,

            "incoterm": incoterm,

            "contact_name": contact_name,

            "first_name": first_name,

            "last_name": last_name,

            "job_title": job_title,

            "department": department,

            "contact_email": contact_email,

            "sender_name": "John Oloche Okpe",

            "sender_title": "Founder & CEO",

            "company_email": "contactperson@reignfarmx.com",

            "company_website": "https://reignfarmx.com"

        }

        subject = Template(
            template.subject
        ).render(**context)

        body = Template(
            template.body
        ).render(**context)

        return subject, body