import logging
from typing import Callable

from asana.constants import Position
from asana.models import AtlasUser
from common import MessageSender
from common.message_sender import UserTag

from comment_notifier.collectors.dto import CommentDto

from .abstract import BaseCommentSender
from .dto import CommentSendMessageResult
from .exceptions import CantNotify
from .registry import register_sender


@register_sender(
    name="SilentSender",
    description="Не отправляет сообщения",
)
class SilentSender(BaseCommentSender):
    def notify(self, comment_dto: CommentDto) -> CommentSendMessageResult:
        _ = comment_dto
        return CommentSendMessageResult(is_send=False, messages=[])


@register_sender(
    name="PersonalSender",
    description="Отправка сообщения в личку упомянутого пользователя",
)
class PersonalSender(BaseCommentSender):
    def notify(self, comment_dto: CommentDto) -> CommentSendMessageResult:
        send_messages = []
        for asana_user in comment_dto.mention_users:
            if asana_user.messenger_code is None:
                reason = f"User {asana_user.user_id} not have message tag to send message"
                self._send_log_cant_notify(comment_dto=comment_dto, reason=reason)
            else:
                task_url = comment_dto.task_data["permalink_url"]
                task_name = comment_dto.task_data["name"]
                message = f"""
                    Task name: {task_name}
                    Task url: {task_url}
                    Comment:
                    {comment_dto.pretty_comment_text}
                    """
                message = self._normalize_message(message)
                send_result = self.message_sender.send_message_to_user(
                    user_tags=[UserTag(asana_user.messenger_code)],
                    message=message,
                )
                send_messages.append(send_result)
        return CommentSendMessageResult(
            is_send=bool(send_messages),
            messages=send_messages,
        )


@register_sender(
    name="SourceProjectSender",
    description="Баерам, менеджерам сообщение в личку, фармерам - в группу фарма, остальные позиции игнорируються",
)
class SourceProjectSender(BaseCommentSender):
    """
    Send personal message for Buyer or manager, if farmer position - send sms to farmers chat.
    """

    def _get_notifier_func(self, asana_user: AtlasUser) -> Callable[[AtlasUser, CommentDto], dict | None]:
        if not all([asana_user.messenger_code, asana_user.position]):
            raise CantNotify(f"User not have position on message code, user {asana_user.user_id}")

        registry: dict[Position, Callable[[AtlasUser, CommentDto], dict | None]] = {
            Position.FARMER: self._notify_farmer,
            Position.MANAGER: self._notify_baer_or_manager,
            Position.BUYER: self._notify_baer_or_manager,
        }

        return registry.get(asana_user.position, self._notify_not_target_position)

    def _notify_farmer(self, asana_user: AtlasUser, comment_dto: CommentDto) -> str:
        _ = asana_user
        task_url = comment_dto.task_data["permalink_url"]
        task_name = comment_dto.task_data["name"]
        message = f"""
            Task name: {task_name}
            Task url: {task_url}
            Comment:
            {comment_dto.pretty_comment_text}
            """
        message = self._normalize_message(message)
        return self.message_sender.send_message(
            handler=MessageSender.FARM_GROUP,
            message=message,
        )

    def _notify_baer_or_manager(self, asana_user: AtlasUser, comment_dto: CommentDto) -> dict:
        task_name = comment_dto.task_data["name"]
        task_url = comment_dto.task_data["permalink_url"]
        message = f"""
            Task name: {task_name}
            Task url: {task_url}
            Comment:
            {comment_dto.pretty_comment_text}
        """
        message = self._normalize_message(message)
        return self.message_sender.send_message_to_user(
            user_tags=[UserTag(asana_user.messenger_code)],
            message=message,
        )

    def _notify_not_target_position(self, asana_user: AtlasUser, comment_dto: CommentDto) -> None:
        pass

    def notify(self, comment_dto: CommentDto) -> CommentSendMessageResult:
        send_messages = []
        for asana_user in comment_dto.mention_users:
            try:
                notifier_func = self._get_notifier_func(asana_user=asana_user)
                logging.info("Notify func: %s", notifier_func.__name__)
                message_send_result = notifier_func(asana_user=asana_user, comment_dto=comment_dto)  # type: ignore[arg-type]
                logging.info("message_send_result: %s", message_send_result)
                send_messages.append(message_send_result)
            except CantNotify as error:
                self._send_log_cant_notify(comment_dto=comment_dto, reason=str(error))
        return CommentSendMessageResult(
            is_send=comment_dto.has_mention,
            messages=send_messages,
        )
