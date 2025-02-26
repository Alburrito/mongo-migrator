import sys
import pytest

from unittest import mock

from mongo_migrator.cli import main


def test_init():
    """Test the init cli."""
    test_args = ["mongo_migration", "init"]
    with mock.patch.object(sys, "argv", test_args):
        with mock.patch("mongo_migrator.cli.init") as init:
            main()
            init.assert_called_once()


def test_create():
    """Test the create subcommand."""
    test_args = ["mongo-migrator", "create", "Test Migration"]
    with mock.patch.object(sys, "argv", test_args):
        with mock.patch("mongo_migrator.cli.create") as mock_create:
            main()
            mock_create.assert_called_once_with(mock.ANY)
            assert mock_create.call_args[0][0].title == "Test Migration"


def test_upgrade():
    """Test the upgrade subcommand."""
    test_args = ["mongo-migrator", "upgrade"]
    with mock.patch.object(sys, "argv", test_args):
        with mock.patch("mongo_migrator.cli.upgrade") as mock_upgrade:
            main()
            mock_upgrade.assert_called_once_with(mock.ANY)


def test_downgrade():
    """Test the downgrade subcommand."""
    test_args = ["mongo-migrator", "downgrade"]
    with mock.patch.object(sys, "argv", test_args):
        with mock.patch("mongo_migrator.cli.downgrade") as mock_downgrade:
            main()
            mock_downgrade.assert_called_once_with(mock.ANY)


def test_history():
    """Test the history subcommand."""
    test_args = ["mongo-migrator", "history"]
    with mock.patch.object(sys, "argv", test_args):
        with mock.patch("mongo_migrator.cli.history") as mock_history:
            main()
            mock_history.assert_called_once_with(mock.ANY)


def test_no_subcommand():
    """Test no subcommand provided."""
    test_args = ["mongo-migrator"]
    with mock.patch.object(sys, "argv", test_args):
        with mock.patch("argparse.ArgumentParser.print_help") as mock_print_help:
            with pytest.raises(SystemExit) as pytest_wrapped_e:
                main()
            mock_print_help.assert_called_once()
            assert pytest_wrapped_e.type == SystemExit
            assert pytest_wrapped_e.value.code == 1
