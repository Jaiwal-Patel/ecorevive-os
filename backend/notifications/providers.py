import requests
from django.conf import settings
from django.core.mail import send_mail


def send_email_message(*, to: str, subject: str, body: str):
    send_mail(subject, body, settings.DEFAULT_FROM_EMAIL, [to], fail_silently=False)


def send_whatsapp_template(*, to: str, template_name: str, body_parameters: list[str]):
    if not settings.WHATSAPP_ENABLED:
        return {"skipped": True, "reason": "WhatsApp is disabled"}
    required = [
        settings.WHATSAPP_GRAPH_API_VERSION,
        settings.WHATSAPP_PHONE_NUMBER_ID,
        settings.WHATSAPP_ACCESS_TOKEN,
    ]
    if not all(required):
        return {"skipped": True, "reason": "WhatsApp credentials are incomplete"}

    url = (
        f"https://graph.facebook.com/{settings.WHATSAPP_GRAPH_API_VERSION}/"
        f"{settings.WHATSAPP_PHONE_NUMBER_ID}/messages"
    )
    components = []
    if body_parameters:
        components = [{
            "type": "body",
            "parameters": [{"type": "text", "text": value} for value in body_parameters],
        }]
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "template",
        "template": {
            "name": template_name,
            "language": {"code": settings.WHATSAPP_TEMPLATE_LANGUAGE},
            "components": components,
        },
    }
    response = requests.post(
        url,
        json=payload,
        headers={
            "Authorization": f"Bearer {settings.WHATSAPP_ACCESS_TOKEN}",
            "Content-Type": "application/json",
        },
        timeout=20,
    )
    response.raise_for_status()
    return response.json()
