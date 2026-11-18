from flask import (Blueprint, render_template, redirect, url_for, flash, request, current_app)
from app.models.company import Company
from app.models.email_log import EmailLog
from datetime import datetime
from sqlalchemy import func
from app.models.company_contact import CompanyContact
from app.services.email_service import EmailService
from app.services.template_service import TemplateService
from app.forms.campaign_recipient_form import CampaignRecipientForm
from app.models.campaign_recipient import CampaignRecipient
from app.models.company import Company

from app.extensions import db

from app.models.campaign_recipient import CampaignRecipient
from app.models.campaign import Campaign
from app.models.email_template import EmailTemplate
from app.services.hostinger_delivery_service import (
    HostingerDeliveryService
)

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



def normalize_email(email):
    """Normalize an email address for consistent comparison."""
    return (email or "").strip().lower()


def find_successful_campaign_log(campaign_id, email):
    """Check whether this campaign was already sent to this email."""
    email = normalize_email(email)

    if not email:
        return None

    return (
        EmailLog.query
        .filter(
            EmailLog.campaign_id == campaign_id,
            func.lower(func.trim(EmailLog.recipient)) == email,
            func.lower(EmailLog.status).in_(
                ["sent", "delivered", "opened"]
            )
        )
        .order_by(EmailLog.id.desc())
        .first()
    )


def contact_can_receive_marketing(contact):
    """Check the contact's marketing permissions."""
    if contact is None:
        return True

    return (
        contact.marketing_allowed is True
        and contact.receive_campaigns is True
        and (contact.status or "Active").lower() == "active"
    )



@campaigns_bp.route("/<int:id>/send", methods=["POST"])
def send_campaign(id):

    campaign = Campaign.query.get_or_404(id)

    if not campaign.template:
        flash("Please assign an email template.", "danger")
        return redirect(
            url_for("campaigns.view_campaign", id=id)
        )

    template = campaign.template

    # Include temporary SMTP failures in the next send attempt.
    # Do not automatically resend Sent, Failed, Skipped, or Unknown.
    recipients = [
        recipient
        for recipient in campaign.recipients
        if recipient.status in [None, "Pending", "Retry Pending"]
        and recipient.sent_at is None
    ]

    if not recipients:
        flash(
            "There are no pending or retryable recipients to send.",
            "info"
        )
        return redirect(
            url_for("campaigns.view_campaign", id=id)
        )

    batch_messages = []
    recipient_map = {}
    seen_emails = set()

    success = 0
    failed = 0
    retry_pending = 0
    unknown = 0
    skipped = 0

    for recipient in recipients:

        company = recipient.company

        if not company:
            recipient.status = "Failed"
            recipient.error_message = "Company record not found."
            failed += 1
            continue

        # Reuse the saved address on retries.
        # Do not silently switch to a different contact.
        if recipient.recipient_email:
            recipient_email = normalize_email(
                recipient.recipient_email
            )

            contact = (
                CompanyContact.query
                .filter(
                    CompanyContact.company_id == company.id,
                    func.lower(func.trim(CompanyContact.email))
                    == recipient_email
                )
                .first()
            )
        else:
            contact = TemplateService.get_best_contact(company)

            if contact:
                recipient_email = normalize_email(contact.email)
            else:
                recipient_email = normalize_email(company.email)

        if not recipient_email:
            recipient.status = "Failed"
            recipient.error_message = (
                "No recipient email address found."
            )
            failed += 1
            continue

        # Respect marketing permissions when a contact record exists.
        if not contact_can_receive_marketing(contact):
            recipient.status = "Skipped"
            recipient.error_message = (
                "Contact is inactive or not eligible for marketing."
            )
            skipped += 1
            continue

        # Duplicate check 1: already sent this campaign to this email.
        previous_log = find_successful_campaign_log(
            campaign.id,
            recipient_email
        )

        if previous_log:
            recipient.recipient_email = recipient_email
            recipient.status = previous_log.status
            recipient.sent_at = (
                recipient.sent_at or previous_log.sent_at
            )
            recipient.error_message = None
            skipped += 1

            print(
                f"SKIPPED DUPLICATE: Campaign {campaign.id} "
                f"already sent to {recipient_email}"
            )
            continue

        # Duplicate check 2: same address repeated in this batch.
        if recipient_email in seen_emails:
            recipient.recipient_email = recipient_email
            recipient.status = "Skipped"
            recipient.error_message = (
                "Duplicate email address in this campaign."
            )
            skipped += 1

            print(
                f"SKIPPED DUPLICATE ADDRESS: {recipient_email}"
            )
            continue

        seen_emails.add(recipient_email)

        # Save the selected address for future retries.
        recipient.recipient_email = recipient_email

        # Render the email.
        try:
            subject, body = TemplateService.render(
                company=company,
                template=template,
                contact=contact
            )

        except Exception as e:
            recipient.status = "Failed"
            recipient.error_message = (
                f"Template rendering failed: {e}"
            )
            failed += 1
            continue

        tracking_url = url_for(
            "campaigns.track_open",
            recipient_id=recipient.id,
            _external=True
        )

        batch_messages.append({
            "recipient": recipient_email,
            "subject": subject,
            "body": body,
            "tracking_url": tracking_url
        })

        recipient_map[recipient_email] = {
            "recipient": recipient,
            "company": company,
            "subject": subject,
            "body": body
        }

    # Save skips and preparation failures if nothing can be sent.
    if not batch_messages:
        db.session.commit()

        flash(
            f"No emails were ready to send. "
            f"{failed} failed, {skipped} skipped.",
            "warning" if failed else "info"
        )

        return redirect(
            url_for("campaigns.view_campaign", id=id)
        )


    # ============================================================
    # SEND AND SAVE IN SMALL BATCHES
    # ============================================================

    batch_size = max(
        1,
        int(current_app.config.get("MAIL_BATCH_SIZE", 20))
    )

    for start in range(0, len(batch_messages), batch_size):

        current_batch = batch_messages[
            start:start + batch_size
        ]

        print(
            f"Sending batch "
            f"{(start // batch_size) + 1} | "
            f"{len(current_batch)} recipients"
        )

        # Each call creates a fresh SMTP connection.
        results = EmailService.send_batch(current_batch)

        for result in results:

            recipient_email = normalize_email(
                result.get("recipient")
            )

            data = recipient_map.get(recipient_email)

            if not data:
                print(
                    f"WARNING: No recipient mapping found for "
                    f"{recipient_email}"
                )
                continue

            recipient = data["recipient"]
            company = data["company"]
            subject = data["subject"]
            body = data["body"]

            success_result = result.get("success", False)
            status = result.get("status", "Failed")
            error = result.get("error")

            recipient.recipient_email = recipient_email

            if success_result:

                recipient.status = "Sent"
                recipient.sent_at = datetime.utcnow()
                recipient.error_message = None

                success += 1

                print(
                    f"SENT: {company.company_name} "
                    f"-> {recipient_email}"
                )

            elif status == "Retry Pending":

                recipient.status = "Retry Pending"
                recipient.sent_at = None
                recipient.error_message = error

                retry_pending += 1

                print(
                    f"TEMPORARY SMTP FAILURE: "
                    f"{company.company_name} "
                    f"-> {recipient_email}: {error}"
                )

            elif status == "Unknown":

                recipient.status = "Unknown"
                recipient.error_message = error

                unknown += 1

                print(
                    f"UNKNOWN DELIVERY STATUS: "
                    f"{company.company_name} "
                    f"-> {recipient_email}: {error}"
                )

            elif status == "Skipped":

                recipient.status = "Skipped"
                recipient.error_message = error

                skipped += 1

            else:

                recipient.status = "Failed"
                recipient.sent_at = None
                recipient.error_message = error

                failed += 1

                print(
                    f"FAILED: {company.company_name} "
                    f"-> {recipient_email}: {error}"
                )

            # Record every attempt.
            log = EmailLog(
                company_id=company.id,
                campaign_id=campaign.id,
                template_id=template.id,
                recipient=recipient_email,
                subject=subject,
                body=body,
                status=status,
                sent_at=(
                    datetime.utcnow()
                    if success_result else None
                ),
                error_message=error
            )

            db.session.add(log)

        # Save completed batch before moving to the next.
        try:

            db.session.commit()

            print(
                f"Batch {(start // batch_size) + 1} "
                f"saved successfully."
            )

        except Exception:

            db.session.rollback()

            current_app.logger.exception(
                "Failed to save campaign batch."
            )

            raise

    flash(
        f"{success} emails sent, {retry_pending} awaiting retry, "
        f"{failed} failed, {unknown} with unknown delivery status, "
        f"{skipped} skipped.",
        "success" if failed == 0 and retry_pending == 0
        and unknown == 0 else "warning"
    )

    return redirect(
        url_for("campaigns.view_campaign", id=id)
    )



@campaigns_bp.route(
    "/track-open/<int:recipient_id>"
)
def track_open(recipient_id):

    recipient = CampaignRecipient.query.get(
        recipient_id
    )

    if recipient:

        recipient.open_count = (
            recipient.open_count or 0
        ) + 1

        if not recipient.opened_at:
            recipient.opened_at = datetime.utcnow()

        if recipient.status in [
            "Pending",
            "Sent",
            "Delivered"
        ]:
            recipient.status = "Opened"

        db.session.commit()

        print(
            f"OPEN TRACKED: "
            f"recipient_id={recipient.id}, "
            f"company={recipient.company.company_name}, "
            f"opens={recipient.open_count}, "
            f"status={recipient.status}"
        )

    else:

        print(
            f"OPEN TRACKING FAILED: "
            f"recipient_id={recipient_id} not found"
        )

    pixel = (
        b"GIF89a"
        b"\x01\x00\x01\x00"
        b"\x80\x00\x00"
        b"\x00\x00\x00"
        b"\xff\xff\xff"
        b"!\xf9\x04\x01"
        b"\x00\x00\x00\x00"
        b",\x00\x00\x00\x00"
        b"\x01\x00\x01\x00"
        b"\x00\x02\x02"
        b"D\x01\x00;"
    )

    return current_app.response_class(
        pixel,
        mimetype="image/gif",
        headers={
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache",
            "Expires": "0"
        }
    )


@campaigns_bp.route("/<int:id>")
def view_campaign(id):

    campaign = Campaign.query.get_or_404(id)

    recipients = (
        CampaignRecipient.query
        .filter_by(campaign_id=campaign.id)
        .order_by(
            CampaignRecipient.id.desc()
        )
        .all()
    )

    total = len(recipients)

    # =========================================================
    # CAMPAIGN COUNTS
    # =========================================================

    sent = sum(
        1
        for r in recipients
        if r.sent_at is not None
    )

    delivered = sum(
        1
        for r in recipients
        if r.delivered_at is not None
    )

    opened = sum(
        1
        for r in recipients
        if r.opened_at is not None
    )

    failed = sum(
        1
        for r in recipients
        if r.status == "Failed"
    )

    pending = sum(
        1
        for r in recipients
        if r.status == "Pending"
    )

    # =========================================================
    # PERFORMANCE RATES
    # =========================================================

    delivery_rate = (
        round(
            (delivered / sent) * 100,
            1
        )
        if sent
        else 0
    )

    open_rate = (
        round(
            (opened / delivered) * 100,
            1
        )
        if delivered
        else 0
    )

    failure_rate = (
        round(
            (failed / sent) * 100,
            1
        )
        if sent
        else 0
    )

    # =========================================================
    # RENDER REPORT
    # =========================================================

    return render_template(
        "campaigns/view.html",
        campaign=campaign,
        total=total,
        sent=sent,
        delivered=delivered,
        opened=opened,
        failed=failed,
        pending=pending,
        delivery_rate=delivery_rate,
        open_rate=open_rate,
        failure_rate=failure_rate,
        recipients=recipients
    )


@campaigns_bp.route("/<int:id>/companies", methods=["GET", "POST"])
def add_companies(id):

    campaign = Campaign.query.get_or_404(id)

    if request.method == "POST":

        company_ids = {int(value)for value in request.form.getlist("company_ids")}

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

@campaigns_bp.route("/<int:id>/recipients", methods=["GET", "POST"])
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

        selected_ids = {
            int(company_id)
            for company_id in form.companies.data
        }

        existing_recipients = CampaignRecipient.query.filter_by(
            campaign_id=campaign.id
        ).all()

        existing_by_company = {
            recipient.company_id: recipient
            for recipient in existing_recipients
        }

        added = 0
        preserved = 0
        removed = 0

        # --------------------------------------------------------
        # Add missing assignments without recreating existing rows
        # --------------------------------------------------------

        for company_id in selected_ids:

            if company_id in existing_by_company:
                preserved += 1
                continue

            company = db.session.get(Company, company_id)

            if not company:
                continue

            recipient = CampaignRecipient(
                campaign_id=campaign.id,
                company_id=company.id,
                status="Pending",
                send_attempt=1
            )

            db.session.add(recipient)
            added += 1

        # --------------------------------------------------------
        # Remove only unselected recipients with no send history
        # --------------------------------------------------------

        for recipient in existing_recipients:

            if recipient.company_id in selected_ids:
                continue

            has_email_logs = EmailLog.query.filter_by(
                campaign_id=campaign.id,
                company_id=recipient.company_id
            ).first() is not None

            has_send_history = (
                has_email_logs
                or recipient.sent_at is not None
                or recipient.delivered_at is not None
                or recipient.opened_at is not None
                or recipient.status in {
                    "Sent",
                    "Delivered",
                    "Opened"
                }
            )

            if has_send_history:
                # Preserve the record to prevent losing send history.
                preserved += 1
                continue

            db.session.delete(recipient)
            removed += 1

        try:
            db.session.commit()

        except Exception:
            db.session.rollback()
            current_app.logger.exception(
                "Failed to update campaign recipients."
            )

            flash(
                "Unable to update campaign recipients.",
                "danger"
            )

            return redirect(
                url_for(
                    "campaigns.view_campaign",
                    id=campaign.id
                )
            )

        flash(
            f"Recipient assignments updated. "
            f"Added: {added}; preserved: {preserved}; "
            f"removed: {removed}.",
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
        recipient.company_id
        for recipient in existing
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

@campaigns_bp.route(
    "/<int:id>/sync-delivery",
    methods=["POST"]
)
def sync_delivery(id):

    campaign = Campaign.query.get_or_404(id)

    try:

        result = (
            HostingerDeliveryService
            .sync_campaign(campaign)
        )

        flash(
            (
                f"Delivery status refreshed. "
                f"Checked: {result['checked']}, "
                f"Delivered: {result['delivered']}, "
                f"Failed: {result['failed']}."
            ),
            "success"
        )

    except Exception as e:

        db.session.rollback()

        flash(
            f"Unable to refresh delivery status: {e}",
            "danger"
        )

    return redirect(
        url_for(
            "campaigns.view_campaign",
            id=campaign.id
        )
    )

@campaigns_bp.route("/<int:id>/resend-unopened", methods=["POST"])
def resend_unopened(id):

    campaign = Campaign.query.get_or_404(id)

    template = campaign.template

    if not template:
        flash(
            "This campaign does not have an email template.",
            "danger"
        )
        return redirect(
            url_for(
                "campaigns.view_campaign",
                id=campaign.id
            )
        )

    recipients = [
        recipient
        for recipient in campaign.recipients
        if (
            recipient.delivered_at is not None
            and recipient.opened_at is None
        )
    ]

    if not recipients:
        flash(
            "There are no delivered recipients without a recorded open.",
            "info"
        )
        return redirect(
            url_for(
                "campaigns.view_campaign",
                id=campaign.id
            )
        )

    success = 0
    failed = 0

    for recipient in recipients:

        company = recipient.company

        if not company:
            recipient.status = "Failed"
            recipient.error_message = (
                "Company record not found."
            )
            failed += 1
            continue

        recipient_email = (
            recipient.recipient_email
            or company.email
        )

        if not recipient_email:
            recipient.status = "Failed"
            recipient.error_message = (
                "Recipient email address not found."
            )
            failed += 1
            continue

        try:

            contact = TemplateService.get_best_contact(
                company
            )

            subject, body = TemplateService.render(
                company=company,
                template=template,
                contact=contact
            )

        except Exception as e:

            recipient.status = "Failed"

            recipient.error_message = (
                f"Template rendering failed: {e}"
            )

            failed += 1

            print(
                f"RESEND TEMPLATE ERROR "
                f"for {company.company_name}: {e}"
            )

            continue

        # -----------------------------------------------------
        # Render the same campaign email
        # -----------------------------------------------------

        try:

            contact = TemplateService.get_best_contact(
                company
            )

            if contact:
                recipient_email = contact.email
            else:
                recipient_email = company.email

            if not recipient_email:
                recipient.status = "Failed"
                recipient.error_message = (
                    "Recipient email address not found."
                )
                failed += 1
                continue

            subject, body = TemplateService.render(
                company=company,
                template=template,
                contact=contact
            )

        except Exception as e:

            recipient.status = "Failed"

            recipient.error_message = (
                f"Template rendering failed: {e}"
            )

            failed += 1

            print(
                f"RESEND TEMPLATE ERROR "
                f"for {company.company_name}: {e}"
            )

            continue

        # -----------------------------------------------------
        # Tracking URL
        # -----------------------------------------------------

        tracking_url = url_for(
            "campaigns.track_open",
            recipient_id=recipient.id,
            _external=True
        )

        # -----------------------------------------------------
        # Send email
        # -----------------------------------------------------

        result = EmailService.send_email(
            recipient=recipient_email,
            subject=subject,
            body=body,
            tracking_url=tracking_url
        )

        success_result = result.get(
            "success",
            False
        )

        status = result.get(
            "status",
            "Failed"
        )

        error = result.get(
            "error"
        )

        # -----------------------------------------------------
        # Update recipient
        # -----------------------------------------------------

        recipient.recipient_email = recipient_email

        recipient.send_attempt = (
            recipient.send_attempt or 1
        ) + 1

        if success_result:

            recipient.status = "Sent"

            recipient.sent_at = datetime.utcnow()

            recipient.delivered_at = None

            recipient.error_message = None

            success += 1

        else:

            recipient.status = "Failed"

            recipient.sent_at = None

            recipient.delivered_at = None

            recipient.error_message = error

            failed += 1

        # -----------------------------------------------------
        # Create email log
        # -----------------------------------------------------

        log = EmailLog(
            company_id=company.id,
            campaign_id=campaign.id,
            template_id=template.id,
            recipient=recipient_email,
            subject=subject,
            body=body,
            status=status,
            error_message=error
        )

        db.session.add(log)

    db.session.commit()

    flash(
        (
            f"Resend completed. "
            f"Successfully sent: {success}. "
            f"Failed: {failed}."
        ),
        "success" if failed == 0 else "warning"
    )

    return redirect(
        url_for(
            "campaigns.view_campaign",
            id=campaign.id
        )
    )

@campaigns_bp.route("/<int:id>/delete", methods=["POST"])
def delete_campaign(id):

    campaign = Campaign.query.get_or_404(id)

    try:

        CampaignRecipient.query.filter_by(
            campaign_id=campaign.id
        ).delete(
            synchronize_session=False
        )

        EmailLog.query.filter_by(
            campaign_id=campaign.id
        ).delete(
            synchronize_session=False
        )

        db.session.delete(campaign)

        db.session.commit()

        flash(
            "Campaign deleted successfully.",
            "success"
        )

    except Exception as e:

        db.session.rollback()

        print("=" * 80)
        print("CAMPAIGN DELETE ERROR")
        print(str(e))
        print("=" * 80)

        flash(
            "Unable to delete campaign.",
            "danger"
        )

    return redirect(
        url_for("campaigns.view_campaign")
    )