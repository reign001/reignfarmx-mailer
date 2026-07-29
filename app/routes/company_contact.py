from flask import (
    Blueprint,
    render_template,
    redirect,
    url_for,
    flash,
)

from app.extensions import db

from app.models.company import Company
from app.models.company_contact import CompanyContact

from app.forms.company_contact_form import CompanyContactForm


company_contact_bp = Blueprint(
    "company_contact",
    __name__,
    url_prefix="/companies/<int:company_id>/contacts"
)

@company_contact_bp.route("/")
def index(company_id):

    company = Company.query.get_or_404(company_id)

    contacts = CompanyContact.query.filter_by(
        company_id=company.id
    ).order_by(
        CompanyContact.is_primary.desc(),
        CompanyContact.first_name
    ).all()

    return render_template(
        "company_contacts/index.html",
        company=company,
        contacts=contacts
    )

@company_contact_bp.route("/add", methods=["GET", "POST"])
def create(company_id):

    company = Company.query.get_or_404(company_id)

    form = CompanyContactForm()

    if form.validate_on_submit():

        if form.is_primary.data:

            CompanyContact.query.filter_by(
                company_id=company.id,
                is_primary=True
            ).update(
                {"is_primary": False}
            )

        contact = CompanyContact(

            company_id=company.id,

            first_name=form.first_name.data,

            last_name=form.last_name.data,

            job_title=form.job_title.data,

            department=form.department.data,

            contact_type=form.contact_type.data,

            email=form.email.data,

            phone=form.phone.data,

            linkedin=form.linkedin.data,

            preferred_contact_method=form.preferred_contact_method.data,

            decision_level=form.decision_level.data,

            is_primary=form.is_primary.data,

            receive_campaigns=form.receive_campaigns.data,

            marketing_allowed=form.marketing_allowed.data,

            status=form.status.data,

            notes=form.notes.data

        )

        db.session.add(contact)

        db.session.commit()

        flash(
            "Contact added successfully.",
            "success"
        )

        return redirect(
            url_for(
                "company.view_company",
                id=company.id
            )
        )

    return render_template(
        "company_contacts/form.html",
        form=form,
        company=company,
        title="Add Contact"
    )

@company_contact_bp.route("/<int:id>/edit", methods=["GET", "POST"])
def edit(company_id, id):

    company = Company.query.get_or_404(company_id)

    contact = CompanyContact.query.get_or_404(id)

    form = CompanyContactForm(obj=contact)

    if form.validate_on_submit():

        if form.is_primary.data:

            CompanyContact.query.filter_by(
                company_id=company.id,
                is_primary=True
            ).update(
                {"is_primary": False}
            )

        form.populate_obj(contact)

        db.session.commit()

        flash(
            "Contact updated successfully.",
            "success"
        )

        return redirect(
            url_for(
                "company.view_company",
                id=company.id
            )
        )

    return render_template(
        "company_contacts/form.html",
        form=form,
        company=company,
        title="Edit Contact"
    )

@company_contact_bp.route("/<int:id>/delete", methods=["POST"])
def delete(company_id, id):

    contact = CompanyContact.query.get_or_404(id)

    db.session.delete(contact)

    db.session.commit()

    flash(
        "Contact deleted successfully.",
        "success"
    )

    return redirect(
        url_for(
            "company.view_company",
            id=company_id
        )
    )

@company_contact_bp.route("/<int:id>/primary", methods=["POST"])
def make_primary(company_id, id):

    CompanyContact.query.filter_by(
        company_id=company_id
    ).update(
        {
            "is_primary": False
        }
    )

    contact = CompanyContact.query.get_or_404(id)

    contact.is_primary = True

    db.session.commit()

    flash(
        "Primary contact updated.",
        "success"
    )

    return redirect(
        url_for(
            "company.view_company",
            id=company_id
        )
    )