import smtplib
import traceback

from email.message import EmailMessage
from flask import current_app
import time



class EmailService:
    @staticmethod
    def _is_connection_error(error):
        """Identify SMTP and underlying network connection failures."""

        return isinstance(
            error,
            (
                smtplib.SMTPServerDisconnected,
                ConnectionError,
                TimeoutError,
                OSError,
            )
        )

    # ============================================================
    # BUILD EMAIL MESSAGE
    # ============================================================

    @staticmethod
    def build_message(
        recipient,
        subject,
        body,
        tracking_url=None
    ):

        sender = current_app.config["MAIL_DEFAULT_SENDER"]

        msg = EmailMessage()

        msg["Subject"] = subject
        msg["From"] = sender
        msg["To"] = recipient

        # --------------------------------------------------------
        # Plain-text version
        # --------------------------------------------------------

        msg.set_content(body)

        # --------------------------------------------------------
        # HTML version
        # --------------------------------------------------------

        html_body = body.replace("\n", "<br>")

        if tracking_url:

            tracking_pixel = f"""
            <img
                src="{tracking_url}"
                width="1"
                height="1"
                style="display:none;"
                alt=""
            >
            """

            html_body += tracking_pixel

        msg.add_alternative(
            html_body,
            subtype="html"
        )

        return msg

    # ============================================================
    # SEND ONE EMAIL
    # ============================================================

    @staticmethod
    def send_email(
        recipient,
        subject,
        body,
        tracking_url=None
    ):

        try:

            server = current_app.config["MAIL_SERVER"]
            port = current_app.config["MAIL_PORT"]
            username = current_app.config["MAIL_USERNAME"]
            password = current_app.config["MAIL_PASSWORD"]

            msg = EmailService.build_message(
                recipient=recipient,
                subject=subject,
                body=body,
                tracking_url=tracking_url
            )

            smtp = smtplib.SMTP_SSL(
                server,
                port, timeout = 30
            )

            try:

                smtp.login(
                    username,
                    password
                )

                smtp.send_message(msg)

            finally:

                smtp.quit()

            return {
                "success": True,
                "status": "Sent",
                "error": None
            }

        except smtplib.SMTPRecipientsRefused as e:

            traceback.print_exc()

            return {
                "success": False,
                "status": "Failed",
                "error": f"Recipient refused: {e}"
            }

        except smtplib.SMTPAuthenticationError as e:

            traceback.print_exc()

            return {
                "success": False,
                "status": "Failed",
                "error": f"SMTP authentication failed: {e}"
            }

        except smtplib.SMTPException as e:

            traceback.print_exc()

            return {
                "success": False,
                "status": "Failed",
                "error": f"SMTP error: {e}"
            }

        except Exception as e:

            traceback.print_exc()

            return {
                "success": False,
                "status": "Failed",
                "error": str(e)
            }



    @staticmethod
    def _get_smtp_code(error):
        """Extract the SMTP response code when one is available."""

        if isinstance(error, smtplib.SMTPRecipientsRefused):
            codes = [
                response[0]
                for response in error.recipients.values()
                if isinstance(response, tuple)
                and response
                and isinstance(response[0], int)
            ]
            return codes[0] if codes else None

        code = getattr(error, "smtp_code", None)
        if isinstance(code, int):
            return code

        if error.args and isinstance(error.args[0], int):
            return error.args[0]

        return None

    @staticmethod
    def _classify_smtp_error(error):
        """
        Return (status, message).

        Retry Pending: a temporary SMTP rejection or a failure known
                       to have occurred before any message was sent.
        Failed:        a permanent SMTP rejection.
        Unknown:       the server may have accepted the message before
                       the connection failed.
        """

        code = EmailService._get_smtp_code(error)
        message = str(error)

        if code is not None and 400 <= code < 500:
            return "Retry Pending", message

        if code is not None and 500 <= code < 600:
            return "Failed", message

        if isinstance(error, smtplib.SMTPAuthenticationError):
            return "Failed", f"SMTP authentication failed: {message}"

        if isinstance(error, smtplib.SMTPServerDisconnected):
            return "Unknown", (
                "SMTP connection closed unexpectedly. "
                "Check delivery records before retrying. "
                f"Details: {message}"
            )

        if isinstance(error, smtplib.SMTPException):
            return "Unknown", (
                "SMTP outcome could not be confirmed. "
                f"Details: {message}"
            )

        return "Unknown", (
            "Delivery outcome could not be confirmed. "
            f"Details: {message}"
        )

    # ============================================================
    # SEND BATCH
    # ============================================================
    @staticmethod
    def send_batch(messages):
        results = []
        seen_recipients = set()
        smtp = None

        # Configurable delay between outgoing messages.
        try:
            delay = max(
                0.0,
                float(current_app.config.get(
                    "MAIL_SEND_DELAY_SECONDS", 10
                ))
            )
        except (TypeError, ValueError):
            delay = 10.0

        # Preserve the input order and ensure one result per input.
        unique_messages = []

        for item in messages:
            recipient = (item.get("recipient") or "").strip()
            normalized = recipient.lower()

            if not normalized:
                results.append({
                    "recipient": recipient,
                    "success": False,
                    "status": "Failed",
                    "error": "Recipient email is empty.",
                })
                continue

            if normalized in seen_recipients:
                results.append({
                    "recipient": recipient,
                    "success": False,
                    "status": "Skipped",
                    "error": "Duplicate recipient in this batch.",
                })
                continue

            seen_recipients.add(normalized)
            unique_messages.append(item)

        if not unique_messages:
            return results

        try:
            server = current_app.config["MAIL_SERVER"]
            port = current_app.config["MAIL_PORT"]
            username = current_app.config["MAIL_USERNAME"]
            password = current_app.config["MAIL_PASSWORD"]

            smtp = smtplib.SMTP_SSL(server, port, timeout = 30)
            smtp.login(username, password)

        except Exception as error:
            traceback.print_exc()
            status, error_message = EmailService._classify_smtp_error(
                error
            )

            # No send_message() call has occurred, so these messages
            # have not been submitted by this batch.
            if status == "Unknown":
                status = "Retry Pending"

            results.extend({
                "recipient": item["recipient"],
                "success": False,
                "status": status,
                "error": error_message,
            } for item in unique_messages)

            if smtp:
                try:
                    smtp.quit()
                except Exception:
                    pass

            return results

        try:
            for index, item in enumerate(unique_messages):
                recipient = item["recipient"]

                try:
                    msg = EmailService.build_message(
                        recipient=recipient,
                        subject=item["subject"],
                        body=item["body"],
                        tracking_url=item.get("tracking_url"),
                    )

                    smtp.send_message(msg)

                    results.append({
                        "recipient": recipient,
                        "success": True,
                        "status": "Sent",
                        "error": None,
                    })

                except Exception as error:
                    traceback.print_exc()
                    status, error_message = (
                        EmailService._classify_smtp_error(error)
                    )

                    results.append({
                        "recipient": recipient,
                        "success": False,
                        "status": status,
                        "error": error_message,
                    })

                    # A broken connection can make later submissions
                    # impossible. Do not try to use a dead connection.
                    if EmailService._is_connection_error(error):
                        remaining = unique_messages[index + 1:]

                        results.extend({
                            "recipient": pending["recipient"],
                            "success": False,
                            "status": "Retry Pending",
                            "error": (
                                "Not attempted because the SMTP "
                                "connection was lost."
                            ),
                        } for pending in remaining)

                        break

                # Space out attempts to reduce rate limiting.
                if index < len(unique_messages) - 1:
                    time.sleep(delay)

        finally:
            if smtp:
                try:
                    smtp.quit()
                except Exception:
                    pass

        return results