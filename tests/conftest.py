import os
import sys
import shutil
from unittest import mock

import mongomock
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))


@pytest.fixture
def mongo_client():
    """Fixture that initializes a in-memory MongoDB client."""
    with mongomock.MongoClient() as client:
        yield client


@pytest.fixture
def mongo_db(mongo_client):
    """Fixture that returns a MongoDB database."""
    yield mongo_client["test_db"]


@pytest.fixture
def mock_config():
    """Fixture that returns a mock configuration."""
    config = mock.MagicMock()
    config.db_host = "localhost"
    config.db_port = 27017
    config.db_name = "test_db"
    config.db_user = "user"
    config.db_password = "password"
    config.mm_collection = "mongo-migrator"
    config.migrations_dir = "/tmp/migrations"
    yield config


@pytest.fixture(autouse=True)
def cleanup(mock_config):
    """Fixture that cleans up the database after each test."""
    yield
    if os.path.exists(mock_config.migrations_dir):
        shutil.rmtree(mock_config.migrations_dir)
