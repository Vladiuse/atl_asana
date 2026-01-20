import logging
from typing import Callable, cast

from asana.constants import Position
from asana.models import AtlasAsanaUser
from message_sender.client import Handlers
from message_sender.models import AtlasUser

from comment_notifier.collectors.dto import CommentDto

from .abstract import BaseCommentSender
from .exceptions import CantNotifyError
from .registry import register_sender


@register_sender(
    name="SilentSender",
    description="Не отправляет сообщения",
)
class SilentSender(BaseCommentSender):
    def notify(self, comment_dto: CommentDto) -> None:
        logging.info("Sender: %s", self.__class__.__name__)
        _ = comment_dto


@register_sender(
    name="LogSender",
    description="Отправка дебаг сообщения",
)
class LogSender(BaseCommentSender):
    def notify(self, comment_dto: CommentDto) -> None:
        logging.info("Sender: %s", self.__class__.__name__)
        task_url = comment_dto.task_data["permalink_url"]
        task_name = comment_dto.task_data["name"]
        message = f"""
            ℹ️ Log message
            Task name: {task_name}
            Task url: {task_url}
            Comment:
            {comment_dto.pretty_comment_text}
            """
        message = self._normalize_message(message)
        self.message_sender.send_log_message(message=message)


@register_sender(
    name="PersonalSender",
    description="Отправка сообщения в личку упомянутого пользователя",
)
class PersonalSender(BaseCommentSender):
    def notify(self, comment_dto: CommentDto) -> None:
        logging.info("Sender: %s", self.__class__.__name__)
        for asana_user in comment_dto.mention_users:
            if asana_user.owner is None or asana_user.owner.tag is None:
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
                self.message_sender.send_message_to_user(
                    user_tag=asana_user.owner.tag,
                    message=message,
                )


@register_sender(
    name="SourceProjectSender",
    description="Баерам, менеджерам сообщение в личку, фармерам - в группу фарма, остальные позиции игнорируются",
)
class SourceProjectSender(BaseCommentSender):
    """Send personal message for Buyer or manager, if farmer position - send sms to farmers chat."""

    def _validate_user_on_send_message(self, asana_user: AtlasAsanaUser) -> None:
        if not asana_user.position:
            raise CantNotifyError(f"Asana user {asana_user} dont have position")
        if not asana_user.owner:
            raise CantNotifyError(f"Asana user {asana_user} dont have chosen owner")
        if not asana_user.owner.tag:
            raise CantNotifyError(f"Asana user {asana_user} owner dont have tag")

    def _get_notifier_func(self, asana_user: AtlasAsanaUser) -> Callable[[AtlasAsanaUser, CommentDto], None]:
        registry: dict[Position, Callable[[AtlasAsanaUser, CommentDto], None]] = {
            Position.FARMER: self._notify_farmer,
            Position.MANAGER: self._notify_bayer_or_manager,
            Position.BUYER: self._notify_bayer_or_manager,
        }
        return registry.get(Position(asana_user.position), self._notify_not_target_position)

    def _notify_farmer(self, asana_user: AtlasAsanaUser, comment_dto: CommentDto) -> None:
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
        self.message_sender.send_message(
            handler=Handlers.FARM_GROUP,
            message=message,
        )

    def _notify_bayer_or_manager(self, asana_user: AtlasAsanaUser, comment_dto: CommentDto) -> None:
        task_name = comment_dto.task_data["name"]
        task_url = comment_dto.task_data["permalink_url"]
        message = f"""
            Task name: {task_name}
            Task url: {task_url}
            Comment:
            {comment_dto.pretty_comment_text}
        """
        message = self._normalize_message(message)
        owner = cast(AtlasUser, asana_user.owner)
        user_tag = cast(str, owner.tag)
        self.message_sender.send_message_to_user(
            user_tag=user_tag,
            message=message,
        )

    def _notify_not_target_position(self, asana_user: AtlasAsanaUser, comment_dto: CommentDto) -> None:
        _, _ = asana_user, comment_dto

    def notify(self, comment_dto: CommentDto) -> None:
        logging.info("Sender: %s", self.__class__.__name__)
        for asana_user in comment_dto.mention_users:
            try:
                self._validate_user_on_send_message(asana_user=asana_user)
                notifier_func = self._get_notifier_func(asana_user=asana_user)
                logging.info("Notify func: %s", notifier_func.__name__)
                notifier_func(asana_user, comment_dto)
            except CantNotifyError as error:
                self._send_log_cant_notify(comment_dto=comment_dto, reason=str(error))
