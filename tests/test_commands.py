from datetime import datetime
import os
import re

from unittest import mock

from mongo_migrator.cli import (
    init as init_command,
    create as create_command,
    upgrade as upgrade_command,
    downgrade as downgrade_command,
    history as history_command,
)


# Utility
def get_migration_params(migration_file_path) -> dict:
    """
    Extract the migration parameters from a migration file.
    Raises:
        ValueError: If the migration file does not contain the required parameters.
    Returns:
        dictionary with the title, version, and last_version.
    """
    with open(migration_file_path, "r") as file:
        migration_content = file.read()

    if any(
        [
            "title:" not in migration_content,
            "version:" not in migration_content,
            "last_version:" not in migration_content,
        ]
    ):
        raise ValueError(f"Invalid migration file: {migration_file_path}")

    title_match = re.search(r"title:\s*(.*)", migration_content)
    version_match = re.search(r"version:\s*(.*)", migration_content)
    last_version_match = re.search(r"last_version:\s*(.*)", migration_content)

    return {
        "title": title_match.group(1),
        "version": version_match.group(1),
        "last_version": last_version_match.group(1),
    }


def get_current_db_version(mongo_db, mock_config) -> str:
    """
    Get the current version of the database.
    Returns:
        The current version of the database.
    """
    documents = list(mongo_db[mock_config.mm_collection].find())
    return documents[0]["current_version"]


def modify_migration(
    migration_file_path: str, upgrade_code: str = None, downgrade_code: str = None
):
    """
    Modifies a file to include the provided upgrade and downgrade code.
    At least one of the upgrade_code or downgrade_code must be provided.
    Or both
    Raises:
        ValueError: If neither upgrade_code nor downgrade_code is provided.
    """
    if not upgrade_code and not downgrade_code:
        raise ValueError(
            "At least one of upgrade_code or downgrade_code must be provided."
        )

    with open(migration_file_path, "r") as file:
        migration_content = file.read()

    if upgrade_code:
        migration_content = re.sub(
            r"def upgrade\(db: Database\):\s+#.*?\s+pass",
            f"def upgrade(db: Database):\n    {upgrade_code}",
            migration_content,
            flags=re.DOTALL,
        )

    if downgrade_code:
        migration_content = re.sub(
            r"def downgrade\(db: Database\):\s+#.*?\s+pass",
            f"def downgrade(db: Database):\n    {downgrade_code}",
            migration_content,
            flags=re.DOTALL,
        )

    with open(migration_file_path, "w") as file:
        file.write(migration_content)


# Tests
def test_init(mock_config, mongo_db):
    """Test the init command."""
    with mock.patch("mongo_migrator.cli.Config", return_value=mock_config):
        # If cannot connect to db, error
        with mock.patch("mongo_migrator.cli.get_db", side_effect=Exception):
            init_command(None)
            assert not os.path.exists(mock_config.migrations_dir)

        with mock.patch("mongo_migrator.cli.get_db", return_value=mongo_db):
            # Call the init command
            init_command(None)

            # Verify collection was successfully created
            assert mock_config.mm_collection in mongo_db.list_collection_names()
            documents = list(mongo_db[mock_config.mm_collection].find())
            # There is only one document in the collection
            assert len(documents) == 1
            assert "current_version" in documents[0]
            # The current version is not set yet since no migrations have been run
            assert documents[0]["current_version"] is None

            # Verify that the migrations directory was created
            assert os.path.exists(mock_config.migrations_dir)


def test_create(mock_config, mongo_db):
    """Test the create command."""
    with mock.patch("mongo_migrator.cli.Config", return_value=mock_config):
        with mock.patch("mongo_migrator.cli.get_db", return_value=mongo_db):
            # If no migration directory exists, error
            args = mock.Mock()
            args.title = "Test migration"
            create_command(args)
            assert not os.path.exists(mock_config.migrations_dir)

            # Initialize the migrator
            init_command(None)

            # Try creating a new migration without title
            args = mock.Mock()
            args.title = None
            create_command(args)
            # assert no files
            assert not os.listdir(mock_config.migrations_dir)

            # Try to create a new migration but the history cant load
            with mock.patch(
                "mongo_migrator.cli.MigrationHistory", side_effect=Exception
            ):
                args.title = "Test migration"
                create_command(args)
                # assert no files
                assert not os.listdir(mock_config.migrations_dir)

            # Try to create a new migration but the history is not empty and not valid
            with mock.patch(
                "mongo_migrator.cli.MigrationHistory.is_empty", return_value=False
            ):
                with mock.patch(
                    "mongo_migrator.cli.MigrationHistory.validate", return_value=False
                ):
                    args.title = "Test migration"
                    create_command(args)
                    # assert no files
                    assert not os.listdir(mock_config.migrations_dir)

            # Create a new correct migration
            # Verify that the migration file was created
            timestamp = datetime.now().strftime("%Y%m%d%H%M")
            test_title = "Test migration"
            args.title = test_title
            create_command(args)
            migration_files = os.listdir(mock_config.migrations_dir)
            migration_files = sorted([f for f in migration_files if f.endswith(".py")])
            assert len(migration_files) == 1

            # Verify that the migration file contains the correct content
            migration_file = migration_files[0]
            migration_file_path = os.path.join(
                mock_config.migrations_dir, migration_file
            )

            mig_params = get_migration_params(migration_file_path)

            assert mig_params["title"] == args.title
            assert mig_params["version"].startswith(timestamp)
            assert mig_params["last_version"] == "None"

            # Create another migration and verify it has the correct last version
            args.title = "Another migration"
            timestamp = datetime.now().strftime("%Y%m%d%H%M")
            create_command(args)
            migration_files = os.listdir(mock_config.migrations_dir)
            migration_files = sorted([f for f in migration_files if f.endswith(".py")])
            assert len(migration_files) == 2

            # Verify that the migration file contains the correct content
            migration_file = migration_files[1]
            migration_file_path = os.path.join(
                mock_config.migrations_dir, migration_file
            )

            second_mig_params = get_migration_params(migration_file_path)

            assert second_mig_params["title"] == args.title
            assert second_mig_params["version"].startswith(timestamp)
            assert second_mig_params["last_version"] == mig_params["version"]


def test_upgrade(mock_config, mongo_db):
    """Test the upgrade command."""
    with mock.patch("mongo_migrator.cli.Config", return_value=mock_config):
        with mock.patch("mongo_migrator.cli.get_db", return_value=mongo_db):
            # If no directory exists, error
            args = mock.Mock()
            args.all = True
            upgrade_command(args)
            assert not os.path.exists(mock_config.migrations_dir)

            # If no current_version exists, error
            os.makedirs(mock_config.migrations_dir)
            upgrade_command(args)
            assert not os.listdir(mock_config.migrations_dir)

            # Initialize the migrator
            init_command(None)

            # If cannot connect to db, error
            with mock.patch("mongo_migrator.cli.get_db", side_effect=Exception):
                upgrade_command(args)
                assert get_current_db_version(mongo_db, mock_config) is None

            # If history cant load, error
            with mock.patch(
                "mongo_migrator.cli.MigrationHistory", side_effect=Exception
            ):
                upgrade_command(args)
                assert get_current_db_version(mongo_db, mock_config) is None

            # Upgrade (all)
            # # if no migrations to run, error
            upgrade_command(args)
            # Check current_version is still None
            assert get_current_db_version(mongo_db, mock_config) is None

            # Create some migrations
            migrations = []
            for i in range(1, 6):
                args = mock.Mock()
                args.title = f"Test migration {i}"
                create_command(args)

            # Get migration info
            migration_files = os.listdir(mock_config.migrations_dir)
            migration_files = sorted([f for f in migration_files if f.endswith(".py")])
            for i, migration_file in enumerate(migration_files):
                migration_file_path = os.path.join(
                    mock_config.migrations_dir, migration_file
                )
                upgrade_code = f"db.create_collection('test_collection_{i+1}')"
                downgrade_code = f"db.drop_collection('test_collection_{i+1}')"
                modify_migration(migration_file_path, upgrade_code, downgrade_code)
                mig_params = get_migration_params(migration_file_path)
                migrations.append(mig_params)

            # if history was not valid, error
            with mock.patch(
                "mongo_migrator.cli.MigrationHistory.validate", return_value=False
            ):
                upgrade_command(args)
                # Check current_version is still None
                assert get_current_db_version(mongo_db, mock_config) is None

            # upgrade (version)
            # # Upgrade to second migration
            args = mock.Mock()
            args.all = False
            args.version = migrations[1]["version"]
            upgrade_command(args)

            # Verify the collection in the 1st 2nd migration was created
            for i in range(1, 3):
                assert f"test_collection_{i}" in mongo_db.list_collection_names()
            # Verify the collection in the 3rd, 4th, and 5th migrations were not created
            for i in range(3, 6):
                assert f"test_collection_{i}" not in mongo_db.list_collection_names()

            # Upgrade to a non pending migration
            args = mock.Mock()
            args.all = False
            args.version = migrations[0]["version"]
            upgrade_command(args)
            # Verify the collection in the 3rd migration was still not created
            assert "test_collection_3" not in mongo_db.list_collection_names()

            # if there was an error running the migration...
            args = mock.Mock()
            args.all = True
            args.version = None
            with mock.patch(
                "mongo_migrator.migration_history.MigrationNode.upgrade",
                side_effect=Exception,
            ):
                upgrade_command(args)
            # Verify the collection in the 3rd migration was still not created
            assert "test_collection_3" not in mongo_db.list_collection_names()
            # Verify the current version is the last applied
            assert (
                get_current_db_version(mongo_db, mock_config)
                == migrations[1]["version"]
            )

            # Upgrade to the end and verify the collection was created
            upgrade_code = "db.create_collection('test_collection_3')"
            downgrade_code = "db.drop_collection('test_collection_3')"
            modify_migration(migration_file_path, upgrade_code, downgrade_code)
            args = mock.Mock()
            args.all = True
            args.version = None
            upgrade_command(args)
            for i in range(1, 6):
                assert f"test_collection_{i}" in mongo_db.list_collection_names()
            # Verify the current version is the last applied
            assert (
                get_current_db_version(mongo_db, mock_config)
                == migrations[-1]["version"]
            )

            # Try to upgrade again
            upgrade_command(args)
            # Verify the current version is still the last applied
            assert (
                get_current_db_version(mongo_db, mock_config)
                == migrations[-1]["version"]
            )


def test_downgrade(mock_config, mongo_db):
    """Test the downgrade command."""
    with mock.patch("mongo_migrator.cli.Config", return_value=mock_config):
        with mock.patch("mongo_migrator.cli.get_db", return_value=mongo_db):
            # If no directory exists, error
            args = mock.Mock()
            args.single = True
            args.all = False
            args.version = None
            downgrade_command(args)
            assert not os.path.exists(mock_config.migrations_dir)

            # If no current_version exists, error
            os.makedirs(mock_config.migrations_dir)
            downgrade_command(args)
            assert not os.listdir(mock_config.migrations_dir)

            # Initialize the migrator
            init_command(None)

            # Create some migrations
            migrations = []
            for i in range(1, 6):
                args = mock.Mock()
                args.title = f"Test migration {i}"
                create_command(args)

            # Get migration info
            migration_files = os.listdir(mock_config.migrations_dir)
            migration_files = sorted([f for f in migration_files if f.endswith(".py")])
            for i, migration_file in enumerate(migration_files):
                migration_file_path = os.path.join(
                    mock_config.migrations_dir, migration_file
                )
                upgrade_code = f"db.create_collection('test_collection_{i+1}')"
                downgrade_code = f"db.drop_collection('test_collection_{i+1}')"
                modify_migration(migration_file_path, upgrade_code, downgrade_code)
                mig_params = get_migration_params(migration_file_path)
                migrations.append(mig_params)

            # If cannot connect to db, error
            with mock.patch("mongo_migrator.cli.get_db", side_effect=Exception):
                downgrade_command(args)
                assert get_current_db_version(mongo_db, mock_config) is None

            # If history cant load, error
            with mock.patch(
                "mongo_migrator.cli.MigrationHistory", side_effect=Exception
            ):
                downgrade_command(args)
                assert get_current_db_version(mongo_db, mock_config) is None

            # If history was not valid, error
            with mock.patch(
                "mongo_migrator.cli.MigrationHistory.validate", return_value=False
            ):
                downgrade_command(args)
                # Check current_version is still None
                assert get_current_db_version(mongo_db, mock_config) is None

            # Downgrade (previous) with no migrations upgraded
            args = mock.Mock()
            args.single = True
            args.all = False
            args.version = None
            downgrade_command(args)
            # Nothing should happen
            assert get_current_db_version(mongo_db, mock_config) is None

            # Run the upgrades
            args = mock.Mock()
            args.all = True
            args.version = None
            upgrade_command(args)
            assert get_current_db_version(mongo_db, mock_config) is not None

            # Downgrade (previous) with all migrations upgraded
            args = mock.Mock()
            args.single = True
            args.all = False
            args.version = None
            downgrade_command(args)
            # Verify the last collection was dropped
            assert "test_collection_5" not in mongo_db.list_collection_names()
            # Verify the current version is the last applied
            assert (
                get_current_db_version(mongo_db, mock_config)
                == migrations[3]["version"]
            )

            # Downgrade to non parent migration, nothing should happen
            args = mock.Mock()
            args.single = False
            args.all = False
            args.version = migrations[-1]["version"]
            downgrade_command(args)
            # Verify the collection in the 4th migration was not dropped
            assert "test_collection_4" in mongo_db.list_collection_names()
            # Verify the current version is still 4th migration
            assert (
                get_current_db_version(mongo_db, mock_config)
                == migrations[3]["version"]
            )

            # Try downgrading to the same version
            args = mock.Mock()
            args.single = False
            args.all = False
            args.version = migrations[3]["version"]
            downgrade_command(args)

            # Downgrade (version)
            args = mock.Mock()
            args.single = False
            args.all = False
            args.version = migrations[2]["version"]
            downgrade_command(args)
            # Verify the collection in the fourth migration was dropped
            assert "test_collection_4" not in mongo_db.list_collection_names()
            # Verify the collection in the third migration was not dropped
            assert "test_collection_3" in mongo_db.list_collection_names()
            # Verify the current version is the third migration
            assert (
                get_current_db_version(mongo_db, mock_config)
                == migrations[2]["version"]
            )

            # If there was an error running the migration...
            args = mock.Mock()
            args.single = False
            args.all = True
            args.version = None
            with mock.patch(
                "mongo_migrator.migration_history.MigrationNode.downgrade",
                side_effect=Exception,
            ):
                downgrade_command(args)
            # Verify the current version is the last applied
            assert (
                get_current_db_version(mongo_db, mock_config)
                == migrations[2]["version"]
            )
            # Verify the collections were not dropped
            for i in range(1, 4):
                assert f"test_collection_{i}" in mongo_db.list_collection_names()

            # Downgrade (all)
            args = mock.Mock()
            args.single = False
            args.all = True
            args.version = None
            downgrade_command(args)
            # Verify all collections were dropped
            for i in range(1, 6):
                assert f"test_collection_{i}" not in mongo_db.list_collection_names()
            # Verify the current version is None
            assert get_current_db_version(mongo_db, mock_config) is None

            # Try to downgrade again
            downgrade_command(args)
            # Verify the current version is still None
            assert get_current_db_version(mongo_db, mock_config) is None


def test_history(mock_config, mongo_db, capfd):
    """Test the history command."""
    with mock.patch("mongo_migrator.cli.Config", return_value=mock_config):
        with mock.patch("mongo_migrator.cli.get_db", return_value=mongo_db):
            # If no directory exists, error
            history_command(None)
            assert not os.path.exists(mock_config.migrations_dir)

            # If no current_version exists, error
            os.makedirs(mock_config.migrations_dir)
            history_command(None)
            assert not os.listdir(mock_config.migrations_dir)

            # Initialize the migrator
            init_command(None)

            migrations = []
            for i in range(1, 6):
                args = mock.Mock()
                args.title = f"Test migration {i}"
                create_command(args)

            # Get migration info
            migration_files = os.listdir(mock_config.migrations_dir)
            migration_files = sorted([f for f in migration_files if f.endswith(".py")])
            for migration_file in migration_files:
                migration_file_path = os.path.join(
                    mock_config.migrations_dir, migration_file
                )
                mig_params = get_migration_params(migration_file_path)
                migrations.append(mig_params)

            # # Run the upgrades
            args = mock.Mock()
            args.all = False
            args.version = migrations[2]["version"]
            upgrade_command(args)
            assert (
                get_current_db_version(mongo_db, mock_config)
                == migrations[2]["version"]
            )

            # If cannot connect to db, error
            with mock.patch("mongo_migrator.cli.get_db", side_effect=Exception):
                history_command(None)

            # If history cant load, error
            with mock.patch(
                "mongo_migrator.cli.MigrationHistory", side_effect=Exception
            ):
                history_command(None)

            # Verify the output
            # First two migrations must be applied
            # Third migration must be current
            # Fourth and fifth migrations must be pending
            # Title and version must match
            expected_output = [
                "[+] Migration history:",
                f'├── (APPLIED) {migrations[0]["version"]} - {migrations[0]["title"]}',
                f'├── (APPLIED) {migrations[1]["version"]} - {migrations[1]["title"]}',
                f'├──>(CURRENT) {migrations[2]["version"]} - {migrations[2]["title"]}',
                f'├── (PENDING) {migrations[3]["version"]} - {migrations[3]["title"]}',
                f'└── (PENDING) {migrations[4]["version"]} - {migrations[4]["title"]}',
            ]
            expected_output_str = "\n".join(expected_output)

            # Capture the output of history_command
            capfd.readouterr()  # Clear any previous captured output
            history_command(None)
            captured = capfd.readouterr()
            assert captured.out.strip() == expected_output_str
