from flask import Blueprint, render_template

from app.models.company import Company
from app.models.email_template import EmailTemplate
from app.models.campaign import Campaign
from app.models.email_log import EmailLog

dashboard_bp = Blueprint(
    "dashboard",
    __name__
)


@dashboard_bp.route("/")
def index():

    return render_template(
        "dashboard/index.html",
        total_companies=Company.query.count(),
        total_templates=EmailTemplate.query.count(),
        total_campaigns=Campaign.query.count(),
        total_sent=EmailLog.query.filter_by(status="Sent").count()
    )