"""
This module handles the history of migrations. It detects bifurcations.
Also comes with functionality to validate the tree.
"""

import importlib.util
import os
import re
import importlib

from typing import Dict, List


class MigrationNode:
    """
    Represents a migration node in the migration history tree.
    """

    def __init__(
        self,
        title: str,
        version: str,
        last_version: str = None,
        upgrade: str = None,
        downgrade: str = None,
    ):
        """
        Create a new migration node.
        Args:
            title: The title of the migration.
            version: The version of the migration.
            last_version: The last version of the migration. None if it is the first migration.
            upgrade: The upgrade function of the migration.
            downgrade: The downgrade function of the migration.
        """
        self.title = title
        self.version = version
        self.last_version = last_version
        self.children: List[MigrationNode] = []
        self._upgrade = upgrade
        self._downgrade = downgrade

    def add_child(self, child_node: "MigrationNode"):
        """
        Add a child node to the current node.
        Args:
            child_node: The child node to add.
        """
        self.children.append(child_node)

    def upgrade(self, db):
        """
        Apply the upgrade function of the migration.
        Args:
            db: The database to upgrade.
        """
        if self._upgrade is not None:
            self._upgrade(db)

    def downgrade(self, db):
        """
        Apply the downgrade function of the migration.
        Args:
            db: The database to downgrade.
        """
        if self._downgrade is not None:
            self._downgrade(db)

    @classmethod
    def from_file(cls, file_path: str) -> "MigrationNode":
        """
        Parse a migration file and return the migration node.
        Args:
            file_path: The path to the migration file.
        Raises:
            FileNotFoundError: If the file is not found.
            ValueError: If the file format is invalid.
        Returns:
            The migration node parsed from the file.
        """
        pattern = re.compile(
            r"""
            title:\s*(?P<title>.+)\n
            version:\s*(?P<version>\d+)\n
            last_version:\s*(?P<last_version>\d+|None)
        """,
            re.VERBOSE,
        )

        # May raise FileNotFoundError
        with open(file_path, "r") as f:
            content = f.read()
            match = pattern.search(content)
            if match is None:
                raise ValueError(f"Invalid migration file format on {file_path}.")
            title = match.group("title")
            version = match.group("version")
            last_version = match.group("last_version")
            last_version = None if last_version == "None" else last_version

            spec = importlib.util.spec_from_file_location("migration_module", file_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            upgrade = getattr(module, "upgrade", None)
            downgrade = getattr(module, "downgrade", None)

            return cls(title, version, last_version, upgrade, downgrade)

    def __repr__(self):
        return (
            f"MigrationNode(title={self.title}, "
            f"version={self.version}, last_version={self.last_version})"
        )

    def __str__(self):
        return f"{self.version} - {self.title}"


class MigrationHistory:

    def __init__(self, migrations_dir: str):
        """
        Class for managing the migration history.
        Args:
            migrations_dir: The directory where the migrations are stored.
        Attributes:
            migrations_dir: The directory where the migrations are stored.
            roots: The root nodes of the migration history.
            migrations: A dictionary of all migrations by version.
        Raises:
            FileNotFoundError: If a migration file is not found.
            ValueError: If a migration file format is invalid.
        """
        self.migrations_dir = migrations_dir
        self.roots: List[MigrationNode] = []
        self.migrations: Dict[str, MigrationNode] = {}
        self._load_migrations()

    def _load_migrations(self):
        """
        Private method to load all migrations from the migrations directory.
        Migrations without a last version or without a found last_version are considered as roots.

        Raises:
            FileNotFoundError: If a migration file is not found.
            ValueError: If a migration file format is invalid.
        """
        migration_files = [
            f for f in os.listdir(self.migrations_dir) if f.endswith(".py")
        ]

        # Load all migration files
        for migration_file in migration_files:
            file_path = os.path.join(self.migrations_dir, migration_file)
            # May raise FileNotFoundError or ValueError
            node = MigrationNode.from_file(file_path)
            self.migrations[node.version] = node
            if node:
                self.migrations[node.version] = node

        # Build the tree
        for node in self.migrations.values():
            if all([node.last_version, node.last_version in self.migrations]):
                self.migrations[node.last_version].add_child(node)
            else:
                self.roots.append(node)

    def is_empty(self) -> bool:
        """
        Check if the migration history is empty.
        Returns:
            True if the history is empty, False otherwise.
        """
        return not self.roots

    def validate(self, node: MigrationNode = None) -> bool:
        """
        Check the migration history for bifurcations.
        The history is valid if it is a non empty linear tree.
        Args:
            node: The node to start the check. If None, the check starts from the root.
        Returns:
            True if the history is valid, False otherwise.
        """
        if self.is_empty():
            return False

        if node is None:
            # More than one root migration
            if len(self.roots) > 1:
                return False
            node = self.roots[0]

        # More than one child for a migration
        if len(node.children) > 1:
            return False

        # Recursive check
        return self.validate(node.children[0]) if node.children else True

    def get_first_version(self) -> str:
        """
        Get the first version of the migration history.
        Assumes that the migration history is valid.
        Returns:
            The first version of the migration history.
        """
        if self.is_empty():
            return None

        return self.roots[0].version

    def get_first_node(self) -> MigrationNode:
        """
        Get the first node of the migration history.
        Assumes that the migration history is valid.
        Returns:
            The first node of the migration history.
        """
        if self.is_empty():
            return None

        return self.roots[0]

    def get_last_version(self) -> str:
        """
        Get the last version of the migration history.
        Assumes that the migration history is valid.
        Returns:
            The last version of the migration history.
        """
        if self.is_empty():
            return None

        current_node = self.roots[0]
        while current_node.children:
            current_node = current_node.children[0]
        return current_node.version

    def get_last_node(self) -> MigrationNode:
        """
        Get the last node of the migration history.
        Assumes that the migration history is valid.
        Returns:
            The last node of the migration history.
        """
        if self.is_empty():
            return None

        current_node = self.roots[0]
        while current_node.children:
            current_node = current_node.children[0]
        return current_node

    def _print_linear_tree(
        self,
        node: MigrationNode,
        current_version: str = None,
        current_found: bool = False,
        is_applied: bool = True,
    ):
        """
        Print a linear tree of the migration history.
        Args:
            node: The node to print.
            level: The level of the node in the tree.
        """
        is_current = current_version == node.version
        current_found = True if is_current else current_found

        # If this is the current version, it is applied
        # Also, every following migration is not applied
        connection = "└──" if not node.children else "├──"
        if is_current:
            state = "(CURRENT) "
            connection += ">"
        else:
            state = " (APPLIED) " if is_applied else " (PENDING) "

        print(f"{connection}{state}{node}")

        if node.children:
            # All migrations before the current version are applied
            if not current_found:
                self._print_linear_tree(
                    node.children[0], current_version, current_found, is_applied
                )
            else:
                self._print_linear_tree(
                    node.children[0], current_version, current_found, False
                )

    def print_history(self, current_version: str = None):
        """
        Prints the history of migrations from oldest to newest.
        Args:
            current_version: The current version of the database.
        Raises:
            ValueError: If the history is invalid.
        """
        if not self.validate():
            raise ValueError("Invalid migration history.")

        first_node = self.get_first_node()

        self._print_linear_tree(
            # Start from the first node
            first_node,
            # Current version to compare
            current_version,
            # If the first node is the current version, the current version is found
            # Therefore, every following migration is not applied
            first_node.version == current_version,
            # If the current version is set, the first migration is applied
            current_version is not None,
        )

    def get_migrations(
        self, start_version: str = None, to_version: str = None
    ) -> List[MigrationNode]:
        """
        Get a list of migrations.
        Assumes that the migration history is valid.
        Args:
            start_version: The version to start from. If None, the first version is used.
            to_version: The last version of the migration list. If None, the last version is used.
        Returns:
            A list of migrations.
        """
        start_version = self.roots[0].version if not start_version else start_version
        to_version = self.get_last_version() if not to_version else to_version

        migrations = []
        version = start_version

        while version != to_version:
            # If the current version is not the target version, add the migration
            current_node = self.migrations[version]
            migrations.append(current_node)
            # If the current version has a child, update the current version
            if current_node.children:
                child = current_node.children[0]
                version = child.version
            else:
                break

        if version == to_version:
            migrations.append(self.migrations[to_version])

        return migrations
