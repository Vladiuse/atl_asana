from asana.webhook_actions.abstract import BaseWebhookAction, WebhookActionResult
from asana.webhook_actions.registry import register_webhook_action


class NotifyTaskCreate(BaseWebhookAction):
    pass