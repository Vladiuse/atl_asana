import logging
from typing import Callable

from asana.constants import Position
from asana.models import AtlasUser
from common import MessageSender
from common.message_sender import UserTag
from common.utils import normalize_multiline

from ..collectors.dto import CommentDto
from .abstract import BaseCommentSender


class SourceProjectSender(BaseCommentSender):
    """
    Comment notifier for "1211350261357695:Общий проект | SOURCE DIV | Запросы и Проблемы" project
    """

    def _get_notifier_func(self, asana_user: AtlasUser) -> Callable[[AtlasUser, CommentDto], dict | None]:
        if not all([asana_user.messenger_code, asana_user.position]):
            return self._notify_not_full_user_data_to_send_message

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
        message = normalize_multiline(message)
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
        message = normalize_multiline(message)
        return self.message_sender.send_message_to_user(
            user_tags=[UserTag(asana_user.messenger_code)],
            message=message,
        )

    def _notify_not_target_position(self, asana_user: AtlasUser, comment_dto: CommentDto) -> None:
        pass

    def _notify_not_full_user_data_to_send_message(self, asana_user: AtlasUser, comment_dto: CommentDto) -> None:
        task_url = comment_dto.task_data["permalink_url"]
        message = f"""
            ⚠️ Упомянут пользователь без должности или тэга мессенджера.
            
            Пользователь:
            Id: {asana_user.user_id}
            Name: {asana_user.name}
            Email: {asana_user.email}
            Task url: {task_url}
        """
        message = normalize_multiline(message)
        self.message_sender.send_log_message(message=message)

    def notify(self, comment_dto: CommentDto) -> None:
        for asana_user in comment_dto.mention_users:
            notifier_func = self._get_notifier_func(asana_user=asana_user)
            logging.info("Notify func: %s", notifier_func.__name__)
            message_send_result = notifier_func(asana_user=asana_user, comment_dto=comment_dto)  # type: ignore[arg-type]
            logging.info("message_send_result: %s", message_send_result)
