"""
This class handles the creation of migration files.

The create_migration_file method creates a new migration file with a template.
This template includes the title, version, and current version of the migration.
"""


class MigrationTemplate:

    TEMPLATE = (
        '"""\n'
        "title: {title}\n"
        "version: {version}\n"
        "last_version: {last_version}\n"
        '"""\n'
        "from pymongo.database import Database\n"
        "\n"
        "def upgrade(db: Database):\n"
        "    # Implement this method in the generated migration file\n"
        "    pass\n"
        "\n"
        "def downgrade(db: Database):\n"
        "    # Implement this method in the generated migration file\n"
        "    pass\n"
        ""
    )

    @classmethod
    def create_migration_file(
        cls, file_path: str, title: str, version: int, last_version: int
    ):
        """
        Create a new migration file.
        Args:
            file_path: The path to the new migration file.
            title: The title of the migration.
            version: The version of the migration.
            last_version: The oldest version of the migrations.
        """
        with open(file_path, "w") as file:
            file.write(
                cls.TEMPLATE.format(
                    title=title, version=version, last_version=last_version
                )
            )
