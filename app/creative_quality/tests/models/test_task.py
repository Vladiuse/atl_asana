import pytest

from creative_quality.models import Creative, CreativeStatus, Task, TaskStatus


@pytest.mark.django_db
class TestTask:
    @pytest.mark.parametrize(
        ("save", "load_failure_count", "status"),
        [
            (True, 1, TaskStatus.ERROR_LOAD_INFO),
            (False, 0, TaskStatus.PENDING),
        ],
    )
    def test_mark_error_load_info(self, save: bool, load_failure_count: int, status: TaskStatus) -> None:
        task = Task.objects.create(task_id="123", status=TaskStatus.PENDING, load_failure_count=0)
        task.mark_error_load_info(save=save)
        task.refresh_from_db()
        assert task.status == status
        assert task.load_failure_count == load_failure_count

    def test_mark_deleted(self) -> None:
        task = Task.objects.create(task_id="123", status=TaskStatus.PENDING, load_failure_count=0)
        creative = Creative.objects.create(task=task)
        task.mark_deleted()
        task.refresh_from_db()
        creative.refresh_from_db()
        assert task.status == TaskStatus.DELETED
        assert creative.status == CreativeStatus.CANCELED

    @pytest.mark.parametrize(("bayer_code", "assignee_id", "is_complete"), [
        ("xxx","xxx", True),
        ("","xxx", False),
        ("xxx","", False),
        ("","", False),
    ])
    def test_is_compete(self, bayer_code: str, assignee_id: str, is_complete: bool) -> None:
        task = Task(task_id="1", bayer_code=bayer_code, assignee_id=assignee_id)
        task.save()
        task.refresh_from_db()
        assert task.is_complete == is_complete
