import logging

from django.db import transaction

from asana.models import WebhookHandler
from asana.webhook_handlers.registry import WEBHOOK_HANDLER_REGISTRY


class WebhookHandlerRegistrySynchronizer:
    @transaction.atomic
    def synchronize(self) -> dict[str, int]:
        sender_names_db = WebhookHandler.objects.values_list("name", flat=True)
        sender_names_register = list(WEBHOOK_HANDLER_REGISTRY)
        to_delete = set(sender_names_db) - set(sender_names_register)
        WebhookHandler.objects.filter(name__in=to_delete).delete()
        logging.info("Senders to delete: %s", to_delete)
        deleted = len(to_delete)
        new_created = 0
        updated = 0
        for sender_name, sender_info in WEBHOOK_HANDLER_REGISTRY.items():
            try:
                sender = WebhookHandler.objects.get(name=sender_name)
                sender.description = sender_info.description
                sender.save()
                updated += 1
            except WebhookHandler.DoesNotExist:
                WebhookHandler.objects.create(
                    name=sender_info.name,
                    description=sender_info.description,
                )
                new_created += 1
        result = {
            "deleted": deleted,
            "new_created": new_created,
            "updated": updated,
        }
        logging.info("Result: %s", result)
        return result
