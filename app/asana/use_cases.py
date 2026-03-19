import logging
from dataclasses import asdict
from typing import Any

from common.message_renderer import render_message
from django.db.models import Q
from message_sender.tasks import send_log_message_task

from asana.repository import AsanaUserRepository

from .models import AtlasAsanaUser

logger = logging.getLogger()


class FetchNewAsanaUsers:
    NOT_FULL_USER_MESSAGE = """
    ⚠️ Find new asana users without owner or position:<br>
    {%for user in users%}
    {{user.name}} id[{{user.pk}}]
    {%endfor%}
"""

    def __init__(self, asana_users_repository: AsanaUserRepository):
        self.asana_users_repository = asana_users_repository

    def execute(self) -> dict[str, Any]:
        result = self.asana_users_repository.update_all()
        logger.debug("Fetch result: %s", result)
        logger.info("Fetch new asana users: %s", result)
        if result.created_count > 0:
            no_position_no_owner_users = (
                AtlasAsanaUser.objects.filter(pk__in=result.created_user_ids)
                .filter(Q(position="") | Q(owner__isnull=True))
            )
            if no_position_no_owner_users:
                logger.warning("No position/owner users found: %s", result.created_user_ids)
                message = render_message(
                    template=self.NOT_FULL_USER_MESSAGE,
                    context={"users": no_position_no_owner_users},
                )
                send_log_message_task.delay(message=message)  # type: ignore[attr-defined]
        return asdict(result)
