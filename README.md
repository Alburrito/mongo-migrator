# Mongo Migrator

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![PyPI version](https://badge.fury.io/py/mongo-migrator.svg)](https://badge.fury.io/py/mongo-migrator)
![Python Versions](https://img.shields.io/pypi/pyversions/mongo-migrator)
![MongoDB](https://img.shields.io/badge/MongoDB-%3E%3D4.0-brightgreen)

![logo](./mongo-migrator.jpg)

## Summary

Mongo Migrator is a simple tool to manage MongoDB migrations. It allows you to create, run, and rollback migrations in a MongoDB database.

## Features

- Easily create migration files with a predefined template.
- Apply migrations to the database.
- Revert migrations quickly.
- Validate and ensure no bifurcations in migration history.
- Keep a clear version history of migrations.


## Installation

To install Mongo-Migrator, you can use **PyPI**:

```bash
pip install mongo-migrator
```

## Configuration

Mongo-Migrator uses a configuration file named `mongo-migrator.config` to connect to your MongoDB instance and manage migrations. Here is an example of a configuration file:

```ini
[database]
host = localhost
port = 27017
name = your_database
user = your_user
password = your_password

[migrations]
directory = migrations
collection = version_history
```

### Configuration breakdown

- **database**: MongoDB connection details.
    - host: MongoDB host address.
    - port: MongoDB port number.
    - name: The database name where migrations will be applied.
    - user: (Optional) The username for database authentication.
    - password: (Optional) The password for database authentication.
- **migrations**: Migration settings.
    - directory: Directory where migration files are stored.
    - collection: Name of the collection that stores migration version information.

## Usage

Mongo-Migrator provides several commands to manage your migrations. These can be executed from the command line.

### Initialize the package

To initialize the package, run the following command:

```bash
mongo_migrator init
```

This command initializes the migration system by reading the configuration file, creating the migrations directory, and setting up the version collection in the specified MongoDB database.

### Create a new migration

To create a new migration, run the following command:

```bash
mongo-migrator create "Added new field"
```

This command generates a new migration file with a timestamp and the provided title. The new migration file will be placed in the migrations directory.

### Apply migrations

```bash
mongo-migrator upgrade
```

This command applies all pending migrations in the correct order. You can also specify a version to upgrade to. The argument `<version>` indicates the last version which will be applied.

```bash
mongo-migrator upgrade --version <version>
```

### Rollback migrations

```bash
mongo-migrator downgrade
```

This command rolls back the last migration that was applied. You can also specify a version to downgrade to. The argument `<version>` indicates the version in which the database will be rolled back. Downgrade in migration `<version>` will not be applied.

```bash
mongo-migrator downgrade --version <version>
```

### View history

```bash
mongo-migrator history
```

This command displays the migration history, showing the version number and the migration message.

### Other commands

- `mongo-migrator [ -h | --help ]`: Display the help message.
- `mongo-migrator [ -v | --version ]`: Display the package version.


## Examples

You can find example projects in the repository [mongo-migrator-examples](https://github.com/Alburrito/mongo-migrator-examples).

There you will find:

- [**example-project**](https://github.com/Alburrito/mongo-migrator-examples/tree/main/example-project): An already initialized project with some migrations created.
- [**test-project**](https://github.com/Alburrito/mongo-migrator-examples/tree/main/test-project): The same project as `example-project` but not initialized. It can be used to test the mongo-migrator package.


# Contributing

By the time, contributions are not being accepted. [Issues](https://github.com/Alburrito/mongo-migrator/issues), on the other hand, will be reviewed and answered.

However, feel free to fork the repository and make your own changes if needed.


# License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

Package by [Álvaro Martín López](https://github.com/Alburrito)

Banner by [Sergio Gallego García](https://www.linkedin.com/in/sergio-gallego-garc%C3%ADa-14379b245/)
