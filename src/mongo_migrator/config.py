"""
Contains the utility to manage the configuration file.

Usage:
```
from config import Config
config = Config() # Loads the configuration
print(config.db_host) # Access the database host
print(config.db_port) # Access the database port
...
```

Available variables in the Config class implementation
"""

import configparser
import os


class Config:
    """Class to handle the configuration file"""

    CONFIG_FILE = "mongo-migrator.config"

    def __init__(self):
        """
        Initialize the Config class.

        Description:
            Loads the configuration file and provides access to the configuration values.
            This file must be named after CONFIG_FILE attribute.
            It also must be placed in the same directory where mongo-migrator is going to be used.

        Exit cases:
            If the configuration file is not found, the program will exit.
            If any of the required sections are missing, the program will exit.
        """
        self.config = configparser.ConfigParser()

        try:
            if not os.path.exists(self.CONFIG_FILE):
                raise FileNotFoundError()

            self.config.read(self.CONFIG_FILE)
            # Database configuration
            self.db_host = self.config.get("database", "host")
            self.db_port = self.config.getint("database", "port")
            self.db_name = self.config.get("database", "name")
            self.db_user = None
            self.db_password = None
            # Migrations configuration
            self.migrations_dir = self.config.get("migrations", "directory")
            self.mm_collection = self.config.get("migrations", "collection")
        except FileNotFoundError:
            print("[F] Configuration file not found.")
            print(
                "[F] Please create a configuration file named 'mongo-migrator.config'."
            )
            print("[F] Exiting...")
            exit(1)
        except configparser.NoSectionError as err:
            print("[F] Configuration file is missing sections.")
            print(err)
            print("[F] Exiting...")
            exit(1)

        try:
            self.db_user = self.config.get("database", "user")
        except configparser.NoOptionError:
            self.db_user = None

        try:
            self.db_password = self.config.get("database", "password")
        except configparser.NoOptionError:
            self.db_password = None
