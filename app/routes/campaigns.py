from flask import Blueprint
from flask import render_template
from flask import redirect
from flask import url_for
from flask import flash
from app.models.company import Company
from app.models.email_log import EmailLog
from datetime import datetime

from app.services.email_service import EmailService
from app.services.template_service import TemplateService
from app.forms.campaign_recipient_form import CampaignRecipientForm
from app.models.campaign_recipient import CampaignRecipient
from app.models.company import Company

from app.extensions import db

from app.models.campaign_recipient import CampaignRecipient
from app.models.campaign import Campaign
from app.models.email_template import EmailTemplate

from app.forms.campaign_form import CampaignForm

campaigns_bp = Blueprint(
    "campaigns",
    __name__,
    url_prefix="/campaigns"
)

@campaigns_bp.route("/")
def list_campaigns():

    campaigns = Campaign.query.order_by(
        Campaign.created_at.desc()
    ).all()

    return render_template(
        "campaigns/list.html",
        campaigns=campaigns
    )


@campaigns_bp.route("/new", methods=["GET", "POST"])
def create_campaign():

    form = CampaignForm()

    form.template.choices = [

        (t.id, t.template_name)

        for t in EmailTemplate.query.order_by(
            EmailTemplate.template_name
        )

    ]

    if form.validate_on_submit():

        campaign = Campaign(
            name=form.campaign_name.data,
            description=form.description.data,
            template_id=form.template.data,
            status=form.status.data
        )

        db.session.add(campaign)

        db.session.commit()

        flash(
            "Campaign created successfully.",
            "success"
        )

        return redirect(
            url_for("campaigns.list_campaigns")
        )

    return render_template(
        "campaigns/form.html",
        form=form
    )

@campaigns_bp.route("/<int:id>/send", methods=["POST"])
def send_campaign(id):

    print("=" * 70)
    print("SEND CAMPAIGN STARTED")
    print("=" * 70)

    campaign = Campaign.query.get_or_404(id)

    print(f"Campaign ID: {campaign.id}")
    print(f"Campaign Name: {campaign.name}")

    if not campaign.template:

        flash(
            "Please assign an email template.",
            "danger"
        )

        return redirect(
            url_for("campaigns.view_campaign", id=id)
        )

    template = campaign.template

    print(f"Template: {template.template_name}")

    recipients = campaign.recipients

    print(f"Recipients Found: {len(recipients)}")

    if not recipients:

        flash(
            "This campaign has no recipients.",
            "warning"
        )

        return redirect(
            url_for("campaigns.add_recipients", id=id)
        )

    success = 0
    failed = 0

    for recipient in recipients:

        print("-" * 70)

        company = recipient.company

        if not company:

            failed += 1
            continue

        print(f"Company : {company.company_name}")

        # ----------------------------------------------------
        # Pick the best contact
        # ----------------------------------------------------

        contact = TemplateService.get_best_contact(company)

        if contact:

            recipient_email = contact.email

            print(f"Contact : {contact.first_name} {contact.last_name}")
            print(f"Job     : {contact.job_title}")
            print(f"Email   : {recipient_email}")

        else:

            recipient_email = company.email

            print("No suitable contact found.")
            print(f"Using company email: {recipient_email}")

        # ----------------------------------------------------
        # Render Template
        # ----------------------------------------------------

        try:

            subject, body = TemplateService.render(

                company=company,

                template=template,

                contact=contact

            )

            print("Template rendered successfully.")

        except Exception as e:

            print("TEMPLATE ERROR:", e)

            recipient.status = "Failed"
            recipient.error_message = str(e)

            failed += 1

            continue

        # ----------------------------------------------------
        # Send Email
        # ----------------------------------------------------

        print("Sending email...")

        ok, error = EmailService.send_email(

            recipient=recipient_email,

            subject=subject,

            body=body

        )

        print(f"Returned from EmailService: ok={ok}")

        if error:
            print(error)

        recipient.status = "Sent" if ok else "Failed"
        recipient.sent_at = datetime.utcnow() if ok else None
        recipient.error_message = error

        log = EmailLog(

            company_id=company.id,

            campaign_id=campaign.id,

            template_id=template.id,

            recipient=recipient_email,

            subject=subject,

            body=body,

            status="Sent" if ok else "Failed",

            error_message=error

        )

        db.session.add(log)

        if ok:
            success += 1
        else:
            failed += 1

    db.session.commit()

    print("=" * 70)
    print("CAMPAIGN COMPLETE")
    print("=" * 70)
    print(f"Success : {success}")
    print(f"Failed  : {failed}")

    flash(
        f"{success} emails sent. {failed} failed.",
        "success"
    )

    return redirect(
        url_for("campaigns.list_campaigns")
    )


@campaigns_bp.route("/<int:id>")
def view_campaign(id):


    campaign = Campaign.query.get_or_404(id)
    total = len(campaign.recipients)

    recipients = CampaignRecipient.query.filter_by(
        campaign_id=id
    ).all()

    sent = sum(
        1 for r in campaign.recipients
        if r.status == "Sent"
    )

    failed = sum(
        1 for r in campaign.recipients
        if r.status == "Failed"
    )

    pending = sum(
        1 for r in campaign.recipients
        if r.status == "Pending"
    )

    return render_template(

            "campaigns/view.html",

            campaign=campaign,

            total=total,

            sent=sent,

            failed=failed,

            pending=pending,

            recipients=recipients

        )


@campaigns_bp.route(
    "/<int:id>/companies",
    methods=["GET", "POST"]
)
def add_companies(id):

    campaign = Campaign.query.get_or_404(id)

    if request.method == "POST":

        company_ids = request.form.getlist("company_ids")

        for company_id in company_ids:

            exists = CampaignRecipient.query.filter_by(
                campaign_id=id,
                company_id=company_id
            ).first()

            if not exists:

                db.session.add(

                    CampaignRecipient(

                        campaign_id=id,

                        company_id=company_id

                    )

                )

        db.session.commit()

        flash(
            "Companies added successfully.",
            "success"
        )

        return redirect(
            url_for(
                "campaigns.view_campaign",
                id=id
            )
        )

    selected = [
        recipient.company_id
        for recipient in campaign.recipients
    ]

    companies = Company.query.filter(
        ~Company.id.in_(selected)
    ).order_by(
        Company.company_name
    ).all()

    return render_template(
        "campaigns/add_companies.html",
        campaign=campaign,
        companies=companies
    )

@campaigns_bp.route(
    "/<int:campaign_id>/recipient/<int:recipient_id>/delete"
)
def remove_company(campaign_id, recipient_id):

    

    recipient = CampaignRecipient.query.get_or_404(
        recipient_id
    )

    db.session.delete(recipient)

    db.session.commit()

    flash(
        "Company removed from campaign.",
        "success"
    )

    return redirect(
        url_for(
            "campaigns.view_campaign",
            id=campaign_id
        )
    )

@campaigns_bp.route(
    "/<int:id>/edit",
    methods=["GET", "POST"]
)
def edit_campaign(id):

    campaign = Campaign.query.get_or_404(id)

    form = CampaignForm(obj=campaign)

    form.template.choices = [
        (t.id, t.template_name)
        for t in EmailTemplate.query.order_by(
            EmailTemplate.template_name
        )
    ]

    if form.validate_on_submit():

        campaign.name = form.campaign_name.data
        campaign.template_id = form.template.data
        campaign.status = form.status.data

        db.session.commit()

        flash(
            "Campaign updated successfully.",
            "success"
        )

        return redirect(
            url_for("campaigns.list_campaigns")
        )

    return render_template(
        "campaigns/form.html",
        form=form,
        title="Edit Campaign"
    )

@campaigns_bp.route(
    "/<int:id>/recipients",
    methods=["GET", "POST"]
)
def add_recipients(id):

    campaign = Campaign.query.get_or_404(id)

    form = CampaignRecipientForm()

    companies = Company.query.order_by(
        Company.company_name
    ).all()

    form.companies.choices = [
        (c.id, f"{c.company_name} ({c.country})")
        for c in companies
    ]

    if form.validate_on_submit():

        CampaignRecipient.query.filter_by(
            campaign_id=campaign.id
        ).delete()

        for company_id in form.companies.data:

            recipient = CampaignRecipient(

                campaign_id=campaign.id,

                company_id=company_id

            )

            db.session.add(recipient)

        db.session.commit()

        flash(
            "Recipients updated successfully.",
            "success"
        )

        return redirect(
            url_for(
                "campaigns.view_campaign",
                id=campaign.id
            )
        )

    existing = CampaignRecipient.query.filter_by(
        campaign_id=campaign.id
    ).all()

    form.companies.data = [
        r.company_id
        for r in existing
    ]

    return render_template(

        "campaigns/recipients.html",

        campaign=campaign,

        form=form

    )

@campaigns_bp.route("/<int:id>/preview")
def preview_campaign(id):

    campaign = Campaign.query.get_or_404(id)

    if not campaign.template:
        flash(
            "This campaign has no email template assigned.",
            "warning"
        )
        return redirect(
            url_for("campaigns.view_campaign", id=id)
        )

    # Use the first recipient for preview
    recipient = campaign.recipients[0] if campaign.recipients else None

    if recipient:
        company = recipient.company

        subject, body = TemplateService.render(
            company,
            campaign.template
        )
    else:
        subject = campaign.template.subject
        body = campaign.template.body

    return render_template(
        "campaigns/preview.html",
        campaign=campaign,
        subject=subject,
        body=body,
        company=recipient.company if recipient else None
    )