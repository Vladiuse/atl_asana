import logging

from message_sender.tasks import send_log_message_task

from asana.repository import AsanaUserRepository

logger = logging.getLogger()


class FetchNewAsanaUsers:
    def __init__(self, asana_users_repository: AsanaUserRepository):
        self.asana_users_repository = asana_users_repository

    def execute(self) -> dict[str, int]:
        result = self.asana_users_repository.update_all()
        logger.info("Fetch new asana users: %s", result)
        if result["new_created"] > 0:
            message = f"ℹ️ Find new asana users: {result['new_created']}"
            send_log_message_task.delay(message=message)  # type: ignore[attr-defined]
        return result
