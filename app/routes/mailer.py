from flask import (
    Blueprint,
    render_template,
    request,
    flash
)

from app.extensions import db

from app.forms.compose_email_form import ComposeEmailForm

from app.models.company import Company
from app.models.email_template import EmailTemplate

from app.services.template_service import TemplateService
from app.services.email_service import EmailService

mailer_bp = Blueprint(
    "mailer",
    __name__,
    url_prefix="/mailer"
)


def load_choices(form):

    form.company.choices = [
        (c.id, c.company_name)
        for c in Company.query.order_by(
            Company.company_name
        )
    ]

    form.template.choices = [
        (t.id, t.template_name)
        for t in EmailTemplate.query.order_by(
            EmailTemplate.template_name
        )
    ]


@mailer_bp.route(
    "/compose",
    methods=["GET", "POST"]
)
def compose():

    form = ComposeEmailForm()

    load_choices(form)

    if form.validate_on_submit():

        company = db.session.get(
            Company,
            form.company.data
        )

        template = db.session.get(
            EmailTemplate,
            form.template.data
        )

        subject, body = TemplateService.render(
            company,
            template
        )

        form.subject.data = subject
        form.body.data = body

        action = request.form.get("action")

        if action == "send":

            success, error = EmailService.send_email(

                recipient=company.email,

                subject=subject,

                body=body

            )

            if success:

                flash(
                    "Email sent successfully.",
                    "success"
                )

            else:

                flash(
                    error,
                    "danger"
                )

    return render_template(
        "mailer/compose.html",
        form=form
    )