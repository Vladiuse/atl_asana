import pytest

from asana.constants import AsanaResourceType
from asana.models import AsanaWebhook, AsanaWebhookRequestData, ProcessingStatus, WebhookHandler
from asana.webhook_handlers.abstract import BaseWebhookHandler, WebhookHandlerResult
from asana.webhook_handlers.dispatcher import WebhookDispatcher, WebhookDispatcherResult
from asana.webhook_handlers.registry import WEBHOOK_HANDLER_REGISTRY, WebhookHandlerInfo


class FakeBaseWebhookHandler(BaseWebhookHandler):
    result = WebhookHandlerResult(
        is_success=True,
        is_target_event=True,
    )

    def handle(self, webhook_data: AsanaWebhookRequestData) -> WebhookHandlerResult:
        _ = webhook_data
        return self.result


class SuccessTargetHandler(FakeBaseWebhookHandler):
    name = "success_target"
    result = WebhookHandlerResult(
        is_success=True,
        is_target_event=True,
    )


class SuccessNotTargetHandler(FakeBaseWebhookHandler):
    name = "success_not_target"
    result = WebhookHandlerResult(
        is_success=True,
        is_target_event=False,
    )


class ErrorHandler(FakeBaseWebhookHandler):
    name = "error_handler"
    result = WebhookHandlerResult(
        is_success=False,
        is_target_event=False,
        error="error",
    )


class RaiseErrorHandler(FakeBaseWebhookHandler):
    name = "raise_error_handler"

    def handle(self, webhook_data: AsanaWebhookRequestData) -> WebhookHandlerResult:
        _ = webhook_data
        msg = "boom"
        raise TypeError(msg)


TEST_HANDLERS = (SuccessTargetHandler, SuccessNotTargetHandler, ErrorHandler, RaiseErrorHandler)


@pytest.fixture(autouse=True)
def test_handler_register(monkeypatch: pytest.MonkeyPatch) -> None:
    WEBHOOK_HANDLER_REGISTRY.clear()
    for handler_class in TEST_HANDLERS:
        info = WebhookHandlerInfo(
            name=handler_class.name,
            description="",
            webhook_handler_class=handler_class,
        )
        monkeypatch.setitem(WEBHOOK_HANDLER_REGISTRY, handler_class.name, info)


@pytest.mark.django_db
class TestWebhookDispatcher:
    @pytest.fixture(autouse=True)
    def setup(self) -> None:
        self.dispatcher = WebhookDispatcher()
        self.webhook_x = AsanaWebhook.objects.create(
            name="xxx",
            resource_id="123",
            resource_type=AsanaResourceType.PROJECT,
        )
        self.webhook_y = AsanaWebhook.objects.create(
            name="yyy",
            resource_id="123",
            resource_type=AsanaResourceType.PROJECT,
        )

    def test_patch_work(self, subtests: pytest.Subtests) -> None:
        for _class in TEST_HANDLERS:
            with subtests.test(msg="x", _class=_class):
                assert _class.name in self.dispatcher.get_registry_dict()

    def test_empty(self) -> None:
        webhook_data = AsanaWebhookRequestData.objects.create(payload={}, headers={}, webhook=self.webhook_x)
        result = self.dispatcher.dispatch(webhook_data=webhook_data)
        expected = WebhookDispatcherResult()
        assert result == expected
        webhook_data.refresh_from_db()
        assert webhook_data.status == ProcessingStatus.NO_HANDLERS
        assert webhook_data.additional_data == {}

    def test_one_handler(self) -> None:
        webhook_handler = WebhookHandler.objects.create(name=SuccessTargetHandler.name)
        self.webhook_x.handlers.add(webhook_handler)
        webhook_data = AsanaWebhookRequestData.objects.create(payload={}, headers={}, webhook=self.webhook_x)
        result = self.dispatcher.dispatch(webhook_data=webhook_data)
        assert result.errors == {}
        assert result.handler_results[SuccessTargetHandler.name] == SuccessTargetHandler.result
        webhook_data.refresh_from_db()
        assert webhook_data.status == ProcessingStatus.SUCCESS
        assert webhook_data.additional_data != {}

    def test_two_handlers(self) -> None:
        webhook_handler_1 = WebhookHandler.objects.create(name=SuccessTargetHandler.name)
        webhook_handler_2 = WebhookHandler.objects.create(name=ErrorHandler.name)
        self.webhook_x.handlers.add(webhook_handler_1, webhook_handler_2)
        webhook_data = AsanaWebhookRequestData.objects.create(payload={}, headers={}, webhook=self.webhook_x)
        result = self.dispatcher.dispatch(webhook_data=webhook_data)
        assert result.errors == {}
        assert result.handler_results[SuccessTargetHandler.name] == SuccessTargetHandler.result
        assert result.handler_results[ErrorHandler.name] == ErrorHandler.result
        webhook_data.refresh_from_db()
        assert webhook_data.status == ProcessingStatus.SUCCESS
        assert webhook_data.additional_data != {}

    def test_raise_error(self) -> None:
        webhook_handler_1 = WebhookHandler.objects.create(name=RaiseErrorHandler.name)
        self.webhook_x.handlers.add(webhook_handler_1)
        webhook_data = AsanaWebhookRequestData.objects.create(payload={}, headers={}, webhook=self.webhook_x)
        result = self.dispatcher.dispatch(webhook_data=webhook_data)
        assert len(result.errors) == 1
        assert len(result.handler_results) == 0
        assert result.errors == {RaiseErrorHandler.name: "boom"}
        webhook_data.refresh_from_db()
        assert webhook_data.status == ProcessingStatus.FAILED
        assert webhook_data.additional_data != {}

    def test_error_with_success(self) -> None:
        webhook_handler_1 = WebhookHandler.objects.create(name=SuccessTargetHandler.name)
        webhook_handler_2 = WebhookHandler.objects.create(name=RaiseErrorHandler.name)
        self.webhook_x.handlers.add(webhook_handler_1, webhook_handler_2)
        webhook_data = AsanaWebhookRequestData.objects.create(payload={}, headers={}, webhook=self.webhook_x)
        result = self.dispatcher.dispatch(webhook_data=webhook_data)
        assert result.errors == {RaiseErrorHandler.name: "boom"}
        assert result.handler_results[SuccessTargetHandler.name] == SuccessTargetHandler.result
        webhook_data.refresh_from_db()
        assert webhook_data.status == ProcessingStatus.PARTIAL
        assert webhook_data.additional_data != {}

    def test_handler_not_exist_in_registry(self) -> None:
        webhook_handler_1 = WebhookHandler.objects.create(name="xxx")
        self.webhook_x.handlers.add(webhook_handler_1)
        webhook_data = AsanaWebhookRequestData.objects.create(payload={}, headers={}, webhook=self.webhook_x)
        result = self.dispatcher.dispatch(webhook_data=webhook_data)
        assert result.handler_results == {}
        assert len(result.errors) == 1
        assert "xxx" in result.errors
        webhook_data.refresh_from_db()
        assert webhook_data.additional_data != {}
