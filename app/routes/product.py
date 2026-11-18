from flask import (
    Blueprint,
    render_template,
    redirect,
    url_for,
    flash,
    request
)

from app.extensions import db
from app.models.product import Product
from app.forms.product_form import ProductForm

product_bp = Blueprint(
    "product",
    __name__,
    url_prefix="/products"
)

@product_bp.route("/")
def index():

    search = request.args.get("search", "")

    query = Product.query

    if search:
        query = query.filter(
            Product.product_name.ilike(f"%{search}%")
        )

    products = query.order_by(
        Product.product_name
    ).all()

    return render_template(
        "products/index.html",
        products=products,
        search=search
    )

@product_bp.route("/create", methods=["GET", "POST"])
def create():

    form = ProductForm()

    if form.validate_on_submit():

        exists = Product.query.filter_by(
            product_name=form.product_name.data.strip()
        ).first()

        if exists:

            flash(
                "Product already exists.",
                "warning"
            )

            return redirect(
                url_for("product.index")
            )

        product = Product(

            product_name=form.product_name.data.strip(),

            description=form.description.data

        )

        db.session.add(product)

        db.session.commit()

        flash(
            "Product created successfully.",
            "success"
        )

        return redirect(
            url_for("product.index")
        )

    return render_template(
        "products/create.html",
        form=form
    )

@product_bp.route("/<int:id>")
def view(id):

    product = Product.query.get_or_404(id)

    return render_template(
        "products/view.html",
        product=product
    )

@product_bp.route(
    "/<int:id>/edit",
    methods=["GET", "POST"]
)
def edit(id):

    product = Product.query.get_or_404(id)

    form = ProductForm(obj=product)

    if form.validate_on_submit():

        product.product_name = form.product_name.data.strip()

        product.description = form.description.data

        db.session.commit()

        flash(
            "Product updated successfully.",
            "success"
        )

        return redirect(
            url_for(
                "product.view",
                id=product.id
            )
        )

    return render_template(
        "products/edit.html",
        form=form,
        product=product
    )

@product_bp.route(
    "/<int:id>/delete",
    methods=["POST"]
)
def delete(id):

    product = Product.query.get_or_404(id)

    if product.company_products:

        flash(
            "Cannot delete a product that is assigned to companies.",
            "danger"
        )

        return redirect(
            url_for("product.index")
        )

    db.session.delete(product)

    db.session.commit()

    flash(
        "Product deleted successfully.",
        "success"
    )

    return redirect(
        url_for("product.index")
    )