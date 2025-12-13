from typing import NoReturn
from unittest.mock import MagicMock

import pytest
import requests
from pytest_socket import disable_socket


def pytest_runtest_setup() -> None:
    disable_socket()


@pytest.fixture(autouse=True, scope="session")
def mock_requests(monkeypatch: pytest.MonkeyPatch) -> None:
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {}

    def fake_request(*args, **kwargs) -> NoReturn:  # noqa
        raise Exception("You make requests!!!")

    monkeypatch.setattr(requests, "get", fake_request)
    monkeypatch.setattr(requests, "post", fake_request)
    monkeypatch.setattr(requests, "put", fake_request)
    monkeypatch.setattr(requests, "delete", fake_request)
    monkeypatch.setattr(requests, "request", fake_request)
