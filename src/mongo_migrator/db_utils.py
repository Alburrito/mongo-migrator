"""Module for database operations."""

from pymongo import MongoClient
from pymongo.database import Database


def get_db(
    db_host: str,
    db_port: int,
    db_name: str,
    db_user: str = None,
    db_pass: str = None,
    verbose: bool = False,
    max_retries: int = 3,
) -> Database:
    """
    Get the database connection using pymongo.
    Args:
        db_host: The hostname of the MongoDB server.
        db_port: The port number of the MongoDB server.
        db_name: The name of the database.
        db_user: The username for the database if needed.
        db_pass: The password for the database if needed.
        verbose: Whether to print messages.
        max_retries: The number of times to retry connecting to the database.
    Raises:
        Exception: If the connection cannot be established.
    Returns:
        The database connection.
    """
    retries = 0
    timeout_ms = 5000

    if verbose:
        print(f"Connecting to MongoDB at {db_host}:{db_port}...")

    while retries < max_retries:
        try:
            client = MongoClient(
                host=db_host,
                port=db_port,
                username=db_user,
                password=db_pass,
                serverSelectionTimeoutMS=timeout_ms,
                socketTimeoutMS=timeout_ms,
                connectTimeoutMS=timeout_ms,
            )
            db = client[db_name]
            db.list_collection_names()
            if verbose:
                print("[+] Connected to database.")
            return db
        except Exception as err:
            print(f"[F] Error connecting to database: {err}")
            retries += 1

    raise Exception(
        "Could not connect to database. Please check your connection details."
    )


def create_version_collection(db: Database, collection_name: str) -> None:
    """
    Create the version collection in the database.
    Args:
        db: The database connection.
        collection_name: The name of the collection.
    """
    if collection_name not in db.list_collection_names():
        db.create_collection(collection_name)
        print(f"[+] Created version collection '{collection_name}'")
    else:
        print(f"[+] Version collection '{collection_name}' already exists")

    if db[collection_name].count_documents({}) == 0:
        db[collection_name].insert_one({"current_version": None})
        print("[+] Inserted current version document.")
    else:
        print("[+] Current version document already exists.")


def set_current_version(db: Database, collection_name: str, version: str) -> None:
    """
    Set the current version.
    Args:
        db: The database connection.
        collection_name: The name of the version collection.
        version: The current version.
    """
    db[collection_name].update_one({}, {"$set": {"current_version": version}})


def get_current_version(db: Database, collection_name: str) -> str:
    """
    Get the current version.
    Args:
        db: The database connection.
        collection_name: The name of the version collection.
    Returns:
        The current version.
    """
    version = db[collection_name].find_one()
    if version:
        return version.get("current_version")
