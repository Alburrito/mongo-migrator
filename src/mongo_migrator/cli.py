"""
Command line interface for the mongo migrator
"""

import argparse
import os
import sys

from datetime import datetime

from mongo_migrator import __version__
from mongo_migrator.config import Config
from mongo_migrator.db_utils import (
    get_db,
    create_version_collection,
    get_current_version,
    set_current_version,
)

from mongo_migrator.migration_template import MigrationTemplate
from mongo_migrator.migration_history import MigrationHistory


def init(args):
    """
    Needs a config file named 'mongo-migrator.config' in the current directory.
    Will create a migrations directory and a migration collection in the database.
    """
    print("[*] Initializing migrations...")
    print("[*] Reading mongo-migrator.config...")

    # May exit if cant be loaded
    config = Config()

    print("[*] Generating migration collection in the database...")
    try:
        db = get_db(
            config.db_host,
            config.db_port,
            config.db_name,
            config.db_user,
            config.db_password,
        )
        create_version_collection(db, config.mm_collection)
    except Exception as err:
        print(f"[F] Error connecting to the database: {err}")
        return

    print("[*] Generating migration directory...")
    if not os.path.exists(config.migrations_dir):
        os.makedirs(config.migrations_dir)
        print(f"[+] Migration directory created at: {config.migrations_dir}")
    else:
        print(f"[+] Migration directory already exists at: {config.migrations_dir}")

    print("[+] Mongo-Migrator initialization complete.")


def create(args):
    """
    Creates a new migration file in the migration directory.
    """
    print("[*] Creating a new migration file...")

    if not args.title:
        print("[F] Missing argument: <title>")
        return

    raw_title = args.title
    title = raw_title.lower().replace(" ", "_")

    # May exit if cant be loaded
    config = Config()

    # Check if the migrations directory exists
    if not os.path.exists(config.migrations_dir):
        print("[!] Migration directory not found.")
        print("[!] Run 'mongo-migrator init' to initialize the migrations.")
        print("[!] Run 'mongo-migrator create <title>' to create a new migration.")
        return

    date = datetime.now()
    version = date.strftime("%Y%m%d%H%M%S%f")
    file_name = f"{version}_{title}.py"
    migration_path = os.path.join(config.migrations_dir, file_name)

    try:
        migration_history = MigrationHistory(config.migrations_dir)
    except Exception as err:
        print(f"[F] Error loading the migration history: {err}")
        return
    if not migration_history.is_empty() and not migration_history.validate():
        print("[F] Migration history is not valid.")
        print("[F] Please fix the migration files before creating a new migration.")
        return
    last_version = migration_history.get_last_version()

    MigrationTemplate.create_migration_file(
        migration_path, raw_title, version, last_version
    )

    print(f"[+] Migration file created at: {migration_path}")


def upgrade(args):
    """
    Upgrades the database to the latest version by default.
    """
    # May exit if cant be loaded
    config = Config()

    # Check if the migrations directory exists
    if not os.path.exists(config.migrations_dir):
        print("[!] Migration directory not found.")
        print("[!] Run 'mongo-migrator init' to initialize the migrations.")
        print("[!] Run 'mongo-migrator create <title>' to create a new migration.")
        return

    # Get current version
    try:
        db = get_db(
            config.db_host,
            config.db_port,
            config.db_name,
            config.db_user,
            config.db_password,
        )
        current_version = get_current_version(db, config.mm_collection)
        new_current_version = current_version
    except Exception as err:
        print(f"[F] Error connecting to the database: {err}")
        return

    try:
        migration_history = MigrationHistory(config.migrations_dir)
    except Exception as err:
        print(f"[F] Error loading the migration history: {err}")
        return
    # Validate the migration history. Must be a linear tree
    if migration_history.is_empty():
        print("[F] No migrations found.")
        print("[F] Run 'mongo-migrator create <title>' to create a new migration.")
        return
    if not migration_history.validate():
        print("[F] Migration history is not valid.")
        print("[F] Please fix the migration files before upgrading the database.")
        return

    # If requested, upgrade to the specified version, else upgrade to the latest
    to_version = args.version if args and args.version else None
    print(f"[+] Current version: {current_version}")
    print(
        f"[*] Upgrading the database to version: {to_version if to_version else 'latest'}"
    )

    # Retrieve the migrations to run
    # These migrations start with the first one found (if no current_version is set)
    # and end with the specified version (if requested) or the latest one found.
    migrations = migration_history.get_migrations(current_version, to_version)
    # Avoid upgrading the current version since it is already up to date
    to_upgrade = [mig for mig in migrations if mig.version != current_version]

    if args.version:
        # Check the requested migration is included in the retrieved migrations
        for mig in to_upgrade:
            if mig.version == args.version:
                break
        else:
            print(f"[F] Migration {args.version} not found in the peniding migrations.")
            return

    # If there are no migrations to run, exit
    if not to_upgrade:
        print("[+] No migrations to run.")
        return

    # Run the migrations
    print(f"[*] Running {len(to_upgrade)} migrations...")
    success = 0
    try:
        for migration in to_upgrade:
            print(f"[*] Running migration: {migration}")
            migration.upgrade(db)
            new_current_version = migration.version
            success += 1
    except Exception as err:
        print(f"[F] Error running migrations: {err}")
        return
    finally:
        print(f"[+] {success}/{len(to_upgrade)} migrations run successfully.")
        # If the current version has changed after trying to run the migrations
        # set the new current version in the database
        if new_current_version != current_version:
            set_current_version(db, config.mm_collection, new_current_version)
            print(f"[+] Current version set to: {new_current_version}")


def downgrade(args):
    """
    Downgrades the database to the previous version by default.
    """
    # May exit if cant be loaded
    config = Config()

    if not os.path.exists(config.migrations_dir):
        print("[!] Migration directory not found.")
        print("[!] Run 'mongo-migrator init' to initialize the migrations.")
        print("[!] Run 'mongo-migrator create <title>' to create a new migration.")
        return

    # Get current version
    try:
        db = get_db(
            config.db_host,
            config.db_port,
            config.db_name,
            config.db_user,
            config.db_password,
        )
        current_version = get_current_version(db, config.mm_collection)
        new_current_version = current_version
    except Exception as err:
        print(f"[F] Error connecting to the database: {err}")
        return

    try:
        migration_history = MigrationHistory(config.migrations_dir)
    except Exception as err:
        print(f"[F] Error loading the migration history: {err}")
        return
    # Validate the migration history. Must be a linear tree
    if migration_history.is_empty():
        print("[F] No migrations found.")
        print("[F] Run 'mongo-migrator create <title>' to create a new migration.")
        return
    if not migration_history.validate():
        print("[F] Migration history is not valid.")
        print("[F] Please fix the migration files before upgrading the database.")
        return
    if current_version is None:
        print("[F] No migrations have been run yet.")
        return

    # If requested, downgrade to the specified version, else downgrade to the previous
    to_version = args.version if args and args.version else None
    full_downgrade = args.all

    print(f"[+] Current version: {current_version}")
    if full_downgrade:
        print("[*] Full downgrade requested.")
    elif to_version:
        print(f"[*] Downgrading the database to version: {to_version}")
    else:
        print("[*] Downgrading the database to the previous version")

    # Retrieve the migrations to run
    # Because its a backward operation, all the migrations from the first one to the current one
    # are retrieved in reverse order.
    migrations = migration_history.get_migrations(None, current_version)
    migrations = migrations[::-1]
    to_downgrade = []
    # Run downgrade all versions
    if full_downgrade:
        to_downgrade = migrations
    # Downgrade to the specified version (not downgrading that version)
    elif to_version:
        # First check if the requested version is in the migration history
        for migration in migrations:
            if migration.version == to_version:
                break
        else:
            print(f"[F] Migration {to_version} not found in the parent migrations.")
            return
        # Get the migrations to run
        for migration in migrations:
            if migration.version != to_version:
                to_downgrade.append(migration)
            else:
                break
    # Run downgrade on the current version to the previous one
    else:
        to_downgrade = [migrations[0]] if len(migrations) > 1 else []

    # If there are no migrations to run, exit
    if not to_downgrade:
        print("[+] No migrations to run.")
        return

    # Run the migrations
    print(f"[*] Running {len(to_downgrade)} migrations...")
    success = 0
    try:
        for migration in to_downgrade:
            print(f"[*] Running migration: {migration}")
            migration.downgrade(db)
            new_current_version = migration.last_version
            success += 1
    except Exception as err:
        print(f"[F] Error running migrations: {err}")
        return
    finally:
        print(f"[+] {success}/{len(to_downgrade)} migrations run successfully.")
        # If the current version has changed after trying to run the migrations
        # set the new current version in the database
        if new_current_version != current_version:
            set_current_version(db, config.mm_collection, new_current_version)
            print(f"[+] Current version set to: {new_current_version}")


def history(args):
    """Shows the migration history."""
    # May exit if cant be loaded
    config = Config()

    # Check if the migrations directory exists
    if not os.path.exists(config.migrations_dir):
        print("[!] Migration directory not found.")
        print("[!] Run 'mongo-migrator init' to initialize the migrations.")
        return

    # Get the current version
    try:
        db = get_db(
            config.db_host,
            config.db_port,
            config.db_name,
            config.db_user,
            config.db_password,
        )
        current_version = get_current_version(db, config.mm_collection)
    except Exception as err:
        print(f"[F] Error connecting to the database: {err}")
        return

    # Load the migration history
    try:
        migration_history = MigrationHistory(config.migrations_dir)
        print("[+] Migration history:")
        migration_history.print_history(current_version)
    except Exception as err:
        print(f"[F] Error loading the migration history: {err}")
        return


def main():
    parser = argparse.ArgumentParser(
        description="Command line interface for the mongo migrator"
    )
    subparsers = parser.add_subparsers()

    # Version and Help options
    parser.add_argument(
        "-v",
        "--version",
        action="version",
        version="%(prog)s " + __version__,
        help="show the version of mongo-migrator.",
    )

    # Subcommand: init
    parser_init = subparsers.add_parser("init", help="set up the mongo-migrator.")
    parser_init.description = init.__doc__
    parser_init.set_defaults(func=init)

    # Subcommand: create
    parser_create = subparsers.add_parser("create", help="create a new migration file.")
    parser_create.description = create.__doc__
    parser_create.add_argument("title", help="title of the migration")
    parser_create.set_defaults(func=create)

    # Subcommand: upgrade
    parser_upgrade = subparsers.add_parser(
        "upgrade", help="upgrade the database by running the migrations."
    )
    parser_upgrade.description = upgrade.__doc__
    parser_upgrade.add_argument(
        "--all", action="store_true", default=True, help="upgrade to the latest version"
    )
    parser_upgrade.add_argument(
        "--version", help="upgrade to the specified version using the timestamp."
    )
    parser_upgrade.set_defaults(func=upgrade)

    # Subcommand: downgrade
    parser_downgrade = subparsers.add_parser(
        "downgrade", help="downgrade the database by running the migrations."
    )
    parser_downgrade.description = downgrade.__doc__
    parser_downgrade.add_argument(
        "--single",
        action="store_true",
        default=True,
        help="downgrade to the previous version",
    )
    parser_downgrade.add_argument(
        "--all", action="store_true", help="downgrade all versions"
    )
    parser_downgrade.add_argument(
        "--version", help="downgrade to the specified version using the timestamp."
    )
    parser_downgrade.set_defaults(func=downgrade)

    # Subcommand: history
    parser_history = subparsers.add_parser(
        "history", help="show the migration history."
    )
    parser_history.description = history.__doc__
    parser_history.set_defaults(func=history)

    # Parse arguments
    args = parser.parse_args()

    # Ensure that func is set before calling it
    if hasattr(args, "func"):
        args.func(args)
    # If no subcommand is provided, show help message
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":  # pragma: no cover
    main()
