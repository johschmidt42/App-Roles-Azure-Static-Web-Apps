import os
from typing import Callable
from unittest.mock import MagicMock

import psycopg2
import pytest
from azure.functions import HttpRequest, HttpResponse
from psycopg2.pool import SimpleConnectionPool


@pytest.fixture
def set_env() -> None:
    os.environ["POSTGRESQL_HOST"] = "POSTGRESQL_HOST"
    os.environ["POSTGRESQL_USER"] = "POSTGRESQL_USER"
    os.environ["POSTGRESQL_PASSWORD"] = "POSTGRESQL_PASSWORD"
    os.environ["POSTGRESQL_DATABASE_NAME"] = "POSTGRESQL_DATABASE_NAME"


@pytest.fixture
def mock_database_connection(monkeypatch):
    mock_connection: MagicMock = MagicMock(spec=SimpleConnectionPool)
    monkeypatch.setattr(
        psycopg2.pool, "SimpleConnectionPool", lambda *args, **kwargs: mock_connection
    )
    return mock_connection


def test_get_env_vars(set_env, mock_database_connection):
    from backend.function_app import get_env_vars

    req: HttpRequest = HttpRequest(method="GET", body=b"", url="/api/env", params={})

    func_call: Callable = get_env_vars.build().get_user_function()
    response: HttpResponse = func_call(req)

    assert response.status_code == 200
