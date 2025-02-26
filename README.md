# Mongo Migrator

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![PyPI version](https://badge.fury.io/py/mongo-migrator.svg)](https://badge.fury.io/py/mongo-migrator)

![Python 3.8](https://img.shields.io/badge/python-3.8-blue.svg)
![MongoDB](https://img.shields.io/badge/mongodb-4.4-blue.svg)

[![Coverage Status](https://coveralls.io/repos/github/Alburrito/mongo-migrator/badge.svg?branch=main)](https://coveralls.io/github/Alburrito/mongo-migrator?branch=main)
[![Build Status](https://travis-ci.com/Alburrito/mongo-migrator.svg?branch=main)](https://travis-ci.com/Alburrito/mongo-migrator)



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

- database: MongoDB connection details.
    - host: MongoDB host address.
    - port: MongoDB port number.
    - name: The database name where migrations will be applied.
    - user: (Optional) The username for database authentication.
    - password: (Optional) The password for database authentication.
- migrations: Migration settings.
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
mongo-migrator create --title "Added new field"
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

- `mongo-migrator --help`: Display the help message.
- `mongo-migrator --version`: Display the package version.


## Test environment

This repository comes with a folder `test-project` which can be run to test the mongo-migrator package. It also contains `example-project`, which is the same small project as `test-project` already initialized and with some migrations made.

The following dependencies are required to run the example project:
- Docker
- Docker Compose
- Python 3.8 or higher
- pipenv

### Setup of the test environment
1. First of all, go to the `test-project` folder and activate the environment:
```bash
cd test-project
export PIPENV_VENV_IN_PROJECT=1 # Optional, but recommended
pipenv shell
pipenv install
```

2. Use the `docker-compose.yml` file to start a MongoDB instance:
```bash
docker-compose up -d
```

3. Run the setup script
```bash
python3 setup-test-db.py
```
The script will create a database called `test-db` and a collection called `test-collection` with some sample data.

4. Now the environment is ready to be tested.


# Contributing

By the time, contributions are not being accepted. However, [issues](https://github.com/Alburrito/mongo-migrator/issues) will be reviewed and answered.

# License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
