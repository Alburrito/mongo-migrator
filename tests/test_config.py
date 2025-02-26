import os
from unittest import mock
import pytest

from mongo_migrator.config import Config

CONFIG_CONTENT = """
[database]
host = localhost
port = 27017
name = test_db
user = test_user
password = test_password

[migrations]
directory = migrations
collection = migration_collection
"""

CONFIG_FILE = "mongo-migrator.config.test"


@pytest.fixture
def create_config_file():
    """Fixture that crates and cleans  temporary config file"""
    with open(CONFIG_FILE, "w") as file:
        file.write(CONFIG_CONTENT)
    yield
    os.remove(CONFIG_FILE)


@mock.patch("mongo_migrator.config.Config.CONFIG_FILE", CONFIG_FILE)
def test_config_loads_ok(create_config_file):
    """Test that the configuration file is loaded correctly"""
    config = Config()

    # Database configuration assertions
    assert config.db_host == "localhost"
    assert config.db_port == 27017
    assert config.db_name == "test_db"
    assert config.db_user == "test_user"
    assert config.db_password == "test_password"

    # Migrations configuration assertions
    assert config.migrations_dir == "migrations"
    assert config.mm_collection == "migration_collection"


@mock.patch("mongo_migrator.config.Config.CONFIG_FILE", CONFIG_FILE)
def test_config_not_found():
    """Test that the program exits when the configuration file is not found"""
    if os.path.exists(CONFIG_FILE):
        os.remove(CONFIG_FILE)

    with pytest.raises(SystemExit) as excinfo:
        Config()

    assert excinfo.value.code == 1


@mock.patch("mongo_migrator.config.Config.CONFIG_FILE", CONFIG_FILE)
def test_config_missing_sections(create_config_file):
    """Test that the program exits when the configuration file is missing sections"""
    config_content = """[database]
host = localhost
port = 27017
name = test_db
"""

    with open(CONFIG_FILE, "w") as file:
        file.write(config_content)

    with pytest.raises(SystemExit) as excinfo:
        Config()

    assert excinfo.value.code == 1


@mock.patch("mongo_migrator.config.Config.CONFIG_FILE", CONFIG_FILE)
def test_config_missing_options(create_config_file):
    """Test that the program does not exit when an option is missing"""
    config_content = """[database]
host = localhost
port = 27017
name = test_db

[migrations]
directory = migrations
collection = migration_collection
"""

    with open(CONFIG_FILE, "w") as file:
        file.write(config_content)

    config = Config()

    assert config.db_user is None
    assert config.db_password is None


@mock.patch("mongo_migrator.config.Config.CONFIG_FILE", CONFIG_FILE)
def test_config_user_pass_are_optional(create_config_file):
    """Test that the program does not exit when user and password are not provided"""
    config_content = """[database]
host = localhost
port = 27017
name = test_db

[migrations]
directory = migrations
collection = migration_collection
"""

    with open(CONFIG_FILE, "w") as file:
        file.write(config_content)

    config = Config()

    assert config.db_user is None
    assert config.db_password is None
