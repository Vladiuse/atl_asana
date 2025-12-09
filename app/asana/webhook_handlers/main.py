from .abstract import BaseWebhookHandler
from .registry import register_webhook_handler
from asana.models import AsanaWebhookRequestData


@register_webhook_handler(
    name="TEst1",
    description="some desc 1",
)
class TestOneHandler(BaseWebhookHandler):

    def handle(self, webhook_data: AsanaWebhookRequestData) -> None:
        pass

@register_webhook_handler(
    name="TEst2",
    description="some desc 2",
)
class TestTwoHandler(BaseWebhookHandler):

    def handle(self, webhook_data: AsanaWebhookRequestData) -> None:
        pass