import logging
import threading
import sys
import requests
from django.conf import settings

logger = logging.getLogger('notifications')

# Define standard templates (matching the format Meta / Twilio require)
TEMPLATES = {
    'order_confirmed': {
        'body': "Hello {name}, your order #{order_id} at Fun with Art has been confirmed! Total amount: ₹{total_amount}. We will notify you when it ships.",
        'variables': ['name', 'order_id', 'total_amount']
    },
    'workshop_booked': {
        'body': "Hi {name}, your payment for \"{workshop_title}\" has been successfully completed on {payment_date} at {payment_time}! Our team will contact you shortly with further details and schedules.",
        'variables': ['name', 'workshop_title', 'payment_date', 'payment_time']
    }
}

def format_phone_number(phone):
    """
    Ensure the phone number is in international E.164 format.
    Standardizes typical 10-digit Indian numbers to +91.
    """
    phone = str(phone).strip().replace(" ", "").replace("-", "")
    if phone.startswith("+"):
        return phone
    if len(phone) == 10 and phone.isdigit():
        return f"+91{phone}"
    # Fallback to appending + if not already present, otherwise return as is
    return phone

def _send_whatsapp_thread(recipient_phone, template_name, variables):
    """
    Internal thread function to dispatch the WhatsApp message asynchronously.
    """
    try:
        template = TEMPLATES.get(template_name)
        if not template:
            logger.error("WhatsApp template '%s' not found.", template_name)
            return

        # Build formatted body for console logging
        formatted_body = template['body'].format(**variables)
        phone_e164 = format_phone_number(recipient_phone)

        provider = getattr(settings, 'WHATSAPP_PROVIDER', 'console').lower()

        if provider == 'twilio':
            account_sid = getattr(settings, 'TWILIO_ACCOUNT_SID', '')
            auth_token = getattr(settings, 'TWILIO_AUTH_TOKEN', '')
            from_number = getattr(settings, 'TWILIO_WHATSAPP_FROM', 'whatsapp:+14155238886')

            if not account_sid or not auth_token:
                logger.warning(
                    "[WhatsApp Twilio] Missing credentials. Falling back to Console Sandbox logging.\n"
                    "Recipient: %s\n"
                    "Message: %s",
                    phone_e164, formatted_body
                )
                _log_to_console(phone_e164, template_name, variables, formatted_body)
                return

            # Invoke Twilio API using standard basic auth
            url = f"https://api.twilio.com/2010-04-01/Accounts/{account_sid}/Messages.json"
            to_number = f"whatsapp:{phone_e164}"
            
            payload = {
                'To': to_number,
                'From': from_number,
                'Body': formatted_body
            }

            response = requests.post(url, data=payload, auth=(account_sid, auth_token))
            
            if response.status_code in (200, 201):
                logger.info(
                    "[WhatsApp Twilio] Sent successfully — To=%s, Template=%s",
                    phone_e164, template_name
                )
            else:
                logger.error(
                    "[WhatsApp Twilio] Failed to send — Status=%d, Error=%s",
                    response.status_code, response.text
                )
                # Fallback to logging
                _log_to_console(phone_e164, template_name, variables, formatted_body)

        else:
            # Default Console Sandbox logging
            _log_to_console(phone_e164, template_name, variables, formatted_body)

    except Exception:
        logger.exception("Failed to dispatch WhatsApp message (non-fatal)")

def _log_to_console(phone, template_name, variables, formatted_body):
    """Log WhatsApp formatted message to server standard logs."""
    logger.info(
        "\n================ WHATSAPP SANDBOX LOG ================\n"
        "To: %s\n"
        "Template: %s\n"
        "Variables: %s\n"
        "Message Body:\n"
        "------------------------------------------------------\n"
        "%s\n"
        "======================================================\n",
        phone, template_name, variables, formatted_body
    )

def send_whatsapp_async(recipient_phone, template_name, variables):
    """
    Public API: Asynchronously dispatch WhatsApp notifications.
    Spawns a background thread to prevent blocking HTTP requests.
    
    Args:
        recipient_phone (str): Recipient's phone number
        template_name (str): Key matching TEMPLATES dict
        variables (dict): Key-value pairs corresponding to template fields
    """
    if not recipient_phone:
        logger.warning("No phone number provided for WhatsApp template '%s'; skipping.", template_name)
        return

    # Check for unit tests
    is_test = 'test' in sys.argv

    if is_test:
        # Run synchronously in tests to avoid race conditions and database locks
        _send_whatsapp_thread(recipient_phone, template_name, variables)
    else:
        thread = threading.Thread(
            target=_send_whatsapp_thread,
            args=(recipient_phone, template_name, variables),
            daemon=True
        )
        thread.start()
