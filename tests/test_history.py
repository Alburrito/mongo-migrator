import os
import re

from unittest import mock

from mongo_migrator.cli import (
    init as init_command,
    create as create_command,
    history as history_command,
)

from mongo_migrator.migration_history import MigrationHistory, MigrationNode


def test_history_invalid_migration(mock_config, mongo_db, capfd):
    """Test the history command with an invalid migration file."""
    with mock.patch("mongo_migrator.cli.Config", return_value=mock_config):
        with mock.patch("mongo_migrator.cli.get_db", return_value=mongo_db):
            # Initialize the migrator
            init_command(None)

            # Create a migration with missing parameters
            args = mock.Mock()
            args.title = "Invalid migration"
            create_command(args)
            migration_files = os.listdir(mock_config.migrations_dir)
            migration_files = sorted([f for f in migration_files if f.endswith(".py")])
            migration_file = migration_files[0]
            migration_file_path = os.path.join(
                mock_config.migrations_dir, migration_file
            )

            # Modify the migration file to remove its parameters
            with open(migration_file_path, "r") as file:
                migration_content = file.read()

            migration_content = re.sub(r"title:\s*(.*)", "", migration_content)
            migration_content = re.sub(r"version:\s*(.*)", "", migration_content)
            migration_content = re.sub(r"last_version:\s*(.*)", "", migration_content)

            with open(migration_file_path, "w") as file:
                file.write(migration_content)

            capfd.readouterr()
            history_command(None)
            captured = capfd.readouterr()
            assert "Invalid migration file format" in captured.out.strip()


def test_migration_node_representation(mock_config):
    """Test the representation of a migration node."""
    migration_node = MigrationNode(
        title="Test migration", version="1", last_version=None
    )
    assert (
        repr(migration_node)
        == "MigrationNode(title=Test migration, version=1, last_version=None)"
    )


def test_is_empty_history(mongo_db, mock_config):
    """Test the is_empty method of MigrationHistory."""
    with mock.patch("mongo_migrator.cli.Config", return_value=mock_config):
        with mock.patch("mongo_migrator.cli.get_db", return_value=mongo_db):
            init_command(None)
            history = MigrationHistory(mock_config.migrations_dir)
            assert history.is_empty()
            noderoot = MigrationNode(
                title="Migration 1", version="1", last_version=None
            )
            history.roots.append(noderoot)
            history.migrations[noderoot.version] = noderoot
            assert not history.is_empty()


def test_validate_history(mongo_db, mock_config):
    """Test the validate function of MigrationHistory."""
    with mock.patch("mongo_migrator.cli.Config", return_value=mock_config):
        with mock.patch("mongo_migrator.cli.get_db", return_value=mongo_db):
            init_command(None)

            # Empty history
            history = MigrationHistory(mock_config.migrations_dir)
            assert not history.validate(), "La historia vacía debería ser inválida."

            # Create migration nodes for the following cases
            noderoot1 = MigrationNode(
                title="Migration 1", version="1", last_version=None
            )
            noderoot2 = MigrationNode(
                title="Migration 1", version="1", last_version="1"
            )

            # If there are several first migrations, the history is invalid
            history.roots.append(noderoot1)
            history.roots.append(noderoot2)
            history.migrations[noderoot1.version] = noderoot1
            history.migrations[noderoot2.version] = noderoot2
            assert not history.validate()

            # If a node has several children, the history is invalid
            node2 = MigrationNode(title="Migration 2", version="2", last_version="1")
            node3 = MigrationNode(title="Migration 3", version="3", last_version="1")
            noderoot1.add_child(node2)
            noderoot1.add_child(node3)
            history.roots = [noderoot1]
            del history.migrations[noderoot2.version]
            history.migrations[node2.version] = node2
            history.migrations[node3.version] = node3
            assert not history.validate()

            # Fix the history and validate it
            history = MigrationHistory(mock_config.migrations_dir)
            noderoot1 = MigrationNode(
                title="Migration 1", version="1", last_version=None
            )
            node2 = MigrationNode(title="Migration 2", version="2", last_version="1")
            node3 = MigrationNode(title="Migration 3", version="3", last_version="2")
            noderoot1.add_child(node2)
            node2.add_child(node3)
            history.roots = [noderoot1]
            history.migrations[noderoot1.version] = noderoot1
            history.migrations[node2.version] = node2
            history.migrations[node3.version] = node3
            assert history.validate()


def test_get_first_version(mongo_db, mock_config):
    """Test the get_first_version function of MigrationHistory."""
    with mock.patch("mongo_migrator.cli.Config", return_value=mock_config):
        with mock.patch("mongo_migrator.cli.get_db", return_value=mongo_db):
            init_command(None)

            # Empty history
            history = MigrationHistory(mock_config.migrations_dir)
            assert history.get_first_version() is None

            # Create migration nodes for the following cases
            noderoot1 = MigrationNode(
                title="Migration 1", version="1", last_version=None
            )
            node2 = MigrationNode(title="Migration 2", version="2", last_version="1")
            node3 = MigrationNode(title="Migration 3", version="3", last_version="2")
            noderoot1.add_child(node2)
            node2.add_child(node3)
            history.roots = [noderoot1]
            history.migrations[noderoot1.version] = noderoot1
            history.migrations[node2.version] = node2
            history.migrations[node3.version] = node3

            assert history.get_first_version() == "1"


def test_get_first_node(mongo_db, mock_config):
    """Test the get_first_node function of MigrationHistory."""
    with mock.patch("mongo_migrator.cli.Config", return_value=mock_config):
        with mock.patch("mongo_migrator.cli.get_db", return_value=mongo_db):
            init_command(None)

            # Empty history
            history = MigrationHistory(mock_config.migrations_dir)
            assert history.get_first_node() is None

            # Create migration nodes for the following cases
            noderoot1 = MigrationNode(
                title="Migration 1", version="1", last_version=None
            )
            node2 = MigrationNode(title="Migration 2", version="2", last_version="1")
            node3 = MigrationNode(title="Migration 3", version="3", last_version="2")
            noderoot1.add_child(node2)
            node2.add_child(node3)
            history.roots = [noderoot1]
            history.migrations[noderoot1.version] = noderoot1
            history.migrations[node2.version] = node2
            history.migrations[node3.version] = node3

            assert history.get_first_node() == noderoot1


def test_get_last_version(mongo_db, mock_config):
    """Test the get_last_version function of MigrationHistory."""
    with mock.patch("mongo_migrator.cli.Config", return_value=mock_config):
        with mock.patch("mongo_migrator.cli.get_db", return_value=mongo_db):
            init_command(None)

            # Empty history
            history = MigrationHistory(mock_config.migrations_dir)
            assert history.get_last_version() is None

            # Create migration nodes for the following cases
            noderoot1 = MigrationNode(
                title="Migration 1", version="1", last_version=None
            )
            node2 = MigrationNode(title="Migration 2", version="2", last_version="1")
            node3 = MigrationNode(title="Migration 3", version="3", last_version="2")
            noderoot1.add_child(node2)
            node2.add_child(node3)
            history.roots = [noderoot1]
            history.migrations[noderoot1.version] = noderoot1
            history.migrations[node2.version] = node2
            history.migrations[node3.version] = node3

            assert history.get_last_version() == "3"


def test_get_last_node(mongo_db, mock_config):
    """Test the get_last_node function of MigrationHistory."""
    with mock.patch("mongo_migrator.cli.Config", return_value=mock_config):
        with mock.patch("mongo_migrator.cli.get_db", return_value=mongo_db):
            init_command(None)

            # Empty history
            history = MigrationHistory(mock_config.migrations_dir)
            assert history.get_last_node() is None

            # Create migration nodes for the following cases
            noderoot1 = MigrationNode(
                title="Migration 1", version="1", last_version=None
            )
            node2 = MigrationNode(title="Migration 2", version="2", last_version="1")
            node3 = MigrationNode(title="Migration 3", version="3", last_version="2")
            noderoot1.add_child(node2)
            node2.add_child(node3)
            history.roots = [noderoot1]
            history.migrations[noderoot1.version] = noderoot1
            history.migrations[node2.version] = node2
            history.migrations[node3.version] = node3

            assert history.get_last_node() == node3


def test_get_migrations(mongo_db, mock_config):
    """Test the get_migrations function of MigrationHistory."""
    with mock.patch("mongo_migrator.cli.Config", return_value=mock_config):
        with mock.patch("mongo_migrator.cli.get_db", return_value=mongo_db):
            init_command(None)

            # Create migration nodes
            history = MigrationHistory(mock_config.migrations_dir)
            noderoot1 = MigrationNode(
                title="Migration 1", version="1", last_version=None
            )
            node2 = MigrationNode(title="Migration 2", version="2", last_version="1")
            node3 = MigrationNode(title="Migration 3", version="3", last_version="2")
            node4 = MigrationNode(title="Migration 4", version="4", last_version="3")
            node5 = MigrationNode(title="Migration 5", version="5", last_version="4")
            noderoot1.add_child(node2)
            node2.add_child(node3)
            node3.add_child(node4)
            node4.add_child(node5)
            history.roots = [noderoot1]
            history.migrations[noderoot1.version] = noderoot1
            history.migrations[node2.version] = node2
            history.migrations[node3.version] = node3
            history.migrations[node4.version] = node4
            history.migrations[node5.version] = node5

            assert history.get_migrations() == [noderoot1, node2, node3, node4, node5]

            assert history.get_migrations(to_version="4") == [
                noderoot1,
                node2,
                node3,
                node4,
            ]

            assert history.get_migrations(start_version="3") == [node3, node4, node5]

            assert history.get_migrations(start_version="2", to_version="4") == [
                node2,
                node3,
                node4,
            ]
