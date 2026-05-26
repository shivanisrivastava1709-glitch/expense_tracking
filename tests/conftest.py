import os
import tempfile

import pytest

import database.db as db_module
from app import app as flask_app
from database.db import init_db


@pytest.fixture()
def app():
    # Create a temporary file to use as an isolated test database.
    # We cannot use ":memory:" because get_db() opens a new connection on every
    # call — each call would get a different, empty in-memory database.
    # A temp file on disk ensures all calls within a test share the same DB.
    fd, tmp_path = tempfile.mkstemp(suffix=".db")
    os.close(fd)  # SQLite manages the file; release the OS file descriptor.

    original_db_path = db_module._DB_PATH
    db_module._DB_PATH = tmp_path

    flask_app.config["TESTING"] = True
    flask_app.config["SECRET_KEY"] = "test-secret"

    with flask_app.app_context():
        init_db()

    yield flask_app

    # Teardown: restore original path and remove the temp file.
    db_module._DB_PATH = original_db_path
    os.unlink(tmp_path)


@pytest.fixture()
def client(app):
    return app.test_client()
