import requests

from datetime import datetime, timezone
from flask import current_app

from app.extensions import db
from app.models import CampaignRecipient


class HostingerDeliveryService:

    BASE_URL = "https://developers.hostinger.com"

    @staticmethod
    def get_outbound_logs(
        from_date=None,
        to_date=None,
        page=1,
        per_page=100
    ):
        """
        Retrieve outbound delivery logs from Hostinger.
        """

        api_token = current_app.config.get(
            "HOSTINGER_API_TOKEN"
        )

        order_id = current_app.config.get(
            "HOSTINGER_ORDER_ID"
        )

        if not api_token:
            raise RuntimeError(
                "HOSTINGER_API_TOKEN is not configured."
            )

        if not order_id:
            raise RuntimeError(
                "HOSTINGER_ORDER_ID is not configured."
            )

        url = (
            f"{HostingerDeliveryService.BASE_URL}"
            f"/api/mail/v1/orders/{order_id}"
            f"/logs/outbound"
        )

        headers = {
            "Authorization": f"Bearer {api_token}",
            "Accept": "application/json"
        }

        params = {
            "page": page,
            "per_page": per_page
        }

        if from_date:
            params["from_date"] = (
                HostingerDeliveryService.to_iso8601(
                    from_date
                )
            )

        if to_date:
            params["to_date"] = (
                HostingerDeliveryService.to_iso8601(
                    to_date
                )
            )

        response = requests.get(
            url,
            headers=headers,
            params=params,
            timeout=30
        )

        response.raise_for_status()

        return response.json()

    @staticmethod
    def to_iso8601(value):
        """
        Convert datetime to RFC3339/ISO8601.
        """

        if value.tzinfo is None:
            value = value.replace(
                tzinfo=timezone.utc
            )

        return value.astimezone(
            timezone.utc
        ).isoformat().replace(
            "+00:00",
            "Z"
        )

    @staticmethod
    def parse_timestamp(value):
        """
        Convert Hostinger timestamp into a
        timezone-naive UTC datetime suitable
        for the existing database fields.
        """

        if not value:
            return None

        try:
            dt = datetime.fromisoformat(
                value.replace(
                    "Z",
                    "+00:00"
                )
            )

            return dt.astimezone(
                timezone.utc
            ).replace(
                tzinfo=None
            )

        except Exception:
            return None

    @staticmethod
    def sync_campaign(campaign):
        """
        Synchronize delivery information for
        all recipients in a campaign.
        """

        recipients = [
            recipient
            for recipient in campaign.recipients
            if (
                recipient.recipient_email
                or (
                    recipient.company
                    and recipient.company.email
                )
            )
            and recipient.sent_at
        ]

        if not recipients:
            return {
                "checked": 0,
                "delivered": 0,
                "failed": 0,
                "updated": 0
            }

        sent_dates = [
            recipient.sent_at
            for recipient in recipients
            if recipient.sent_at
        ]

        earliest_sent = min(sent_dates)

        logs = []
        page = 1

        while True:

            result = (
                HostingerDeliveryService.get_outbound_logs(
                    from_date=earliest_sent,
                    page=page,
                    per_page=100
                )
            )

            batch = result.get(
                "data",
                []
            )

            logs.extend(batch)

            meta = result.get(
                "meta",
                {}
            )

            current_page = meta.get(
                "current_page",
                page
            )

            total_pages = (
                meta.get("total_pages")
            )

            if total_pages:
                if current_page >= total_pages:
                    break
            else:
                if len(batch) < 100:
                    break

            page += 1

        updated = 0
        delivered = 0
        failed = 0

        for recipient in recipients:

            email = (
                recipient.recipient_email
                or (
                    recipient.company.email
                    if recipient.company
                    else ""
                )
            )

            email = email.strip().lower()

            if not email:
                continue

            if not recipient.recipient_email:
                recipient.recipient_email = email

            matching_logs = []

            for log in logs:

                log_email = (
                    log.get("rcpt")
                    or log.get("rcpts")
                    or ""
                )

                if isinstance(
                    log_email,
                    str
                ):
                    log_email = (
                        log_email
                        .strip()
                        .lower()
                    )

                if log_email != email:
                    continue

                timestamp = (
                    HostingerDeliveryService
                    .parse_timestamp(
                        log.get("timestamp")
                    )
                )

                if not timestamp:
                    continue

                if timestamp < recipient.sent_at:
                    continue

                matching_logs.append(
                    (
                        timestamp,
                        log
                    )
                )

            if not matching_logs:
                continue

            matching_logs.sort(
                key=lambda item: item[0],
                reverse=True
            )

            timestamp, log = (
                matching_logs[0]
            )

            hostinger_status = (
                log.get("status")
            )

            if hostinger_status == "Delivered":

                recipient.delivered_at = (
                    timestamp
                )

                if not recipient.opened_at:
                    recipient.status = "Delivered"

                recipient.error_message = None

                delivered += 1
                updated += 1

            elif hostinger_status == "Failed":

                recipient.status = "Failed"

                recipient.error_message = (
                    HostingerDeliveryService
                    .get_failure_reason(
                        log
                    )
                )

                failed += 1
                updated += 1

        db.session.commit()

        return {
            "checked": len(recipients),
            "delivered": delivered,
            "failed": failed,
            "updated": updated
        }

    @staticmethod
    def get_failure_reason(log):
        """
        Extract the most useful failure information
        from Hostinger relay events.
        """

        relay_events = log.get(
            "relay_events",
            []
        )

        if relay_events:

            latest_event = relay_events[-1]

            response = latest_event.get(
                "response"
            )

            if response:
                return response

            dsn = latest_event.get(
                "dsn"
            )

            if dsn:
                return f"DSN: {dsn}"

        return (
            "Hostinger reported delivery failure."
        )