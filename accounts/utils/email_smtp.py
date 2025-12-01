# accounts/utils/email_smtp.py
import logging
import smtplib
from email.message import EmailMessage
from django.conf import settings

logger = logging.getLogger(__name__)

def send_via_smtplib(to_email, subject, plain_text, html=None, from_email=None, timeout=20):
    """
    Send an email via smtplib using settings from settings.py.
    Returns dict {'ok': True} or {'ok': False, 'error': '...','detail': '...'}
    """
    if not from_email:
        from_email = getattr(settings, "DEFAULT_FROM_EMAIL", settings.EMAIL_SMTP_USER)

    # normalize recipient list
    if not to_email:
        return {"ok": False, "error": "No recipient provided."}
    if isinstance(to_email, str):
        to_list = [to_email]
    else:
        to_list = list(to_email)

    msg = EmailMessage()
    msg["From"] = from_email
    msg["To"] = ", ".join(to_list)
    msg["Subject"] = subject
    msg.set_content(plain_text)
    if html:
        msg.add_alternative(html, subtype="html")

    host = getattr(settings, "EMAIL_SMTP_HOST", None)
    port = getattr(settings, "EMAIL_SMTP_PORT", None)
    user = getattr(settings, "EMAIL_SMTP_USER", None)
    password = getattr(settings, "EMAIL_SMTP_PASSWORD", None)
    use_tls = getattr(settings, "EMAIL_SMTP_USE_TLS", False)
    use_ssl = getattr(settings, "EMAIL_SMTP_USE_SSL", False)

    if not host or not port:
        return {"ok": False, "error": "SMTP host/port not configured."}

    try:
        if use_ssl:
            server = smtplib.SMTP_SSL(host, port, timeout=timeout)
        else:
            server = smtplib.SMTP(host, port, timeout=timeout)

        server.ehlo()
        if use_tls and not use_ssl:
            server.starttls()
            server.ehlo()

        if user and password:
            server.login(user, password)

        server.send_message(msg)
        server.quit()
        return {"ok": True}
    except smtplib.SMTPAuthenticationError as e:
        logger.exception("SMTP authentication error")
        return {"ok": False, "error": "SMTP authentication failed", "detail": str(e)}
    except smtplib.SMTPException as e:
        logger.exception("SMTP error")
        return {"ok": False, "error": "SMTP error", "detail": str(e)}
    except Exception as e:
        logger.exception("Unexpected error sending email")
        return {"ok": False, "error": "Unexpected error", "detail": str(e)}

