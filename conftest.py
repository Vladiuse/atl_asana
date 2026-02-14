import pytest
from pytest_socket import disable_socket
from rest_framework.test import APIClient


def pytest_runtest_setup() -> None:
    disable_socket()


@pytest.fixture
def api_client() -> APIClient:
    return APIClient()
