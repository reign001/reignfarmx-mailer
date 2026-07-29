from flask import (
    Blueprint,
    render_template,
    redirect,
    url_for,
    flash
)
from app.models.email_log import EmailLog

from app.extensions import db
from app.models.campaign import Campaign

from app.forms.email_template_form import EmailTemplateForm

from app.models.email_template import EmailTemplate


templates_bp = Blueprint(
    "templates",
    __name__,
    url_prefix="/templates"
)


@templates_bp.route("/")
def list_templates():

    templates = EmailTemplate.query.order_by(
        EmailTemplate.template_name
    ).all()

    return render_template(
        "templates/index.html",
        templates=templates
    )


@templates_bp.route("/new", methods=["GET", "POST"])
def create_template():

    form = EmailTemplateForm()

    if form.validate_on_submit():

        template = EmailTemplate(

            template_name=form.template_name.data,

            subject=form.subject.data,

            body=form.body.data

        )

        db.session.add(template)

        db.session.commit()

        flash(
            "Template created successfully.",
            "success"
        )

        return redirect(
            url_for("templates.list_templates")
        )

    return render_template(
        "templates/form.html",
        form=form
    )

@templates_bp.route("/<int:id>")
def view_template(id):

    template = EmailTemplate.query.get_or_404(id)

    return render_template(
        "templates/view.html",
        template=template
    )

@templates_bp.route(
    "/<int:id>/edit",
    methods=["GET", "POST"]
)
def edit_template(id):

    template = EmailTemplate.query.get_or_404(id)

    form = EmailTemplateForm(obj=template)

    if form.validate_on_submit():

        template.template_name = form.template_name.data
        template.subject = form.subject.data
        template.body = form.body.data

        db.session.commit()

        flash(
            "Template updated successfully.",
            "success"
        )

        return redirect(
            url_for(
                "templates.list_templates"
            )
        )

    return render_template(
        "templates/form.html",
        form=form,
        title="Edit Template"
    )


@templates_bp.route("/<int:id>/delete", methods=["POST"])
def delete_template(id):

    template = EmailTemplate.query.get_or_404(id)

    # Delete all email logs that used this template
    EmailLog.query.filter_by(
        template_id=template.id
    ).delete(synchronize_session=False)

    # Remove the template from any campaigns
    Campaign.query.filter_by(
        template_id=template.id
    ).update(
        {"template_id": None},
        synchronize_session=False
    )

    # Delete the template
    db.session.delete(template)

    db.session.commit()

    flash(
        "Template deleted successfully.",
        "success"
    )

    return redirect(
        url_for("templates.list_templates")
    )