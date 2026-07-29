from flask import Blueprint, render_template, request, redirect, url_for, flash
from app.models import Company
from app.forms.company_form import CompanyForm
from app.extensions import db

company_bp = Blueprint(
    "company",
    __name__,
    url_prefix="/companies"
)

@company_bp.route("/")
def index():

    page = request.args.get(
        "page",
        1,
        type=int
    )

    search = request.args.get(
        "search",
        ""
    )

    query = Company.query

    if search:

        query = query.filter(
            Company.company_name.ilike(
                f"%{search}%"
            )
        )

    companies = query.order_by(
        Company.company_name
    ).paginate(
        page=page,
        per_page=20
    )

    return render_template(
        "companies/index.html",
        companies=companies,
        search=search
    )


@company_bp.route("/new", methods=["GET", "POST"])
def create_company():

    form = CompanyForm()

    if request.method == "POST":
        print("POST Request Received")
        print(form.errors)

    if form.validate_on_submit():

        try:

            company = Company(

                company_name=form.company_name.data.strip(),

                country=form.country.data.strip(),

                state=form.state.data.strip() if form.state.data else None,

                city=form.city.data.strip() if form.city.data else None,

                email=form.email.data.strip().lower(),

                website=form.website.data.strip() if form.website.data else None,

                products=form.products.data.strip() if form.products.data else None,

                notes=form.notes.data.strip() if form.notes.data else None

            )

            db.session.add(company)

            db.session.commit()

            flash(
                "Company added successfully.",
                "success"
            )

            return redirect(
                url_for("company.index")
            )

        except Exception as e:

            db.session.rollback()

            print(e)

            flash(
                str(e),
                "danger"
            )

    return render_template(
        "companies/form.html",
        form=form
    )





@company_bp.route("/")
def list_companies():

    search = request.args.get(
        "search",
        ""
    )

    query = Company.query

    if search:

        query = query.filter(
            Company.company_name.ilike(
                f"%{search}%"
            )
        )

    companies = query.order_by(
        Company.company_name
    ).all()

    return render_template(
        "companies/list.html",
        companies=companies,
        search=search
    )

@company_bp.route("/<int:id>/edit", methods=["GET", "POST"])
def edit_company(id):

    company = Company.query.get_or_404(id)

    form = CompanyForm(obj=company)

    if form.validate_on_submit():

        form.populate_obj(company)

        db.session.commit()

        flash(
            "Company updated successfully.",
            "success"
        )

        return redirect(
            url_for("company.index")
        )

    return render_template(
        "companies/form.html",
        form=form,
        title="Edit Company"
    )

@company_bp.route("/<int:id>/delete", methods=["POST"])
def delete_company(id):

    company = Company.query.get_or_404(id)
    

    db.session.delete(company)

    db.session.commit()

    flash(
        "Company deleted successfully.",
        "success"
    )

    return redirect(
        url_for("company.index")
    )

@company_bp.route("/<int:id>")
def view_company(id):

    company = Company.query.get_or_404(id)

    return render_template(
        "companies/view.html",
        company=company
    )