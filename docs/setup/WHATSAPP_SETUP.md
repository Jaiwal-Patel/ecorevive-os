# Optional WhatsApp Cloud API Setup

EcoRevive OS starts with WhatsApp disabled. Email and the in-app status history remain the reliable baseline.

## Prerequisites

- a Meta business portfolio;
- a WhatsApp Business Account;
- a registered sending phone number;
- an approved message template for status updates;
- an access token stored outside Git.

## Configuration

Set in `.env.production`:

```text
WHATSAPP_ENABLED=true
WHATSAPP_GRAPH_API_VERSION=vXX.X
WHATSAPP_PHONE_NUMBER_ID=...
WHATSAPP_ACCESS_TOKEN=...
WHATSAPP_TEMPLATE_STATUS_UPDATED=ecorevive_status_updated
WHATSAPP_TEMPLATE_LANGUAGE=en_US
```

The current provider adapter sends template messages only. Keep user consent, template approval and opt-out handling documented before enabling production delivery.
