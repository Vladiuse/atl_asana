from message_sender.tasks import send_log_message_task

from asana.repository import AsanaUserRepository


class FetchNewAsanaUsers:

    def __init__(self, asana_users_repository: AsanaUserRepository):
        self.asana_users_repository = asana_users_repository

    def execute(self) -> dict:
        result = self.asana_users_repository.update_all()
        if result["new_created"] > 0:
            message = f'Find new asana users: {result["new_created"]}'
            send_log_message_task.delay(message=message)
        return result
