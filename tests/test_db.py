import pytest
from unittest import mock
from datetime import datetime

from mongo_migrator.db_utils import (
    get_db,
    create_version_collection,
    set_current_version,
)


def test_get_db_success(mongo_client, mock_config):
    """Test successful connection to the database."""
    with mock.patch("mongo_migrator.db_utils.MongoClient", return_value=mongo_client):
        db = get_db(
            db_host=mock_config.db_host,
            db_port=mock_config.db_port,
            db_name=mock_config.db_name,
            db_user=mock_config.db_user,
            db_pass=mock_config.db_password,
            verbose=True,
        )

        assert db.name == mock_config.db_name


def test_get_db_failure(mock_config):
    """Test failure to connect to the database."""
    with pytest.raises(Exception, match="Could not connect to database"):
        get_db(
            db_host=mock_config.db_host,
            db_port=mock_config.db_port,
            db_name=mock_config.db_name,
            db_user=mock_config.db_user,
            db_pass=mock_config,
        )


def test_create_version_collection(mongo_db, mock_config):
    """Test creation of the version collection."""
    create_version_collection(mongo_db, mock_config.mm_collection)
    assert mock_config.mm_collection in mongo_db.list_collection_names()
    assert mongo_db[mock_config.mm_collection].count_documents({}) == 1
    assert mongo_db[mock_config.mm_collection].find_one().get("current_version") is None


def test_create_version_collection_already_exists(mongo_db, mock_config):
    """Test behavior when the version collection already exists."""
    mongo_db.create_collection(mock_config.mm_collection)
    create_version_collection(mongo_db, mock_config.mm_collection)
    assert mock_config.mm_collection in mongo_db.list_collection_names()


def test_create_version_collection_already_exists_with_data(mongo_db, mock_config):
    """Test behavior when the version collection already exists with data."""
    mongo_db.create_collection(mock_config.mm_collection)
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S%f")
    mongo_db[mock_config.mm_collection].insert_one({"current_version": timestamp})
    create_version_collection(mongo_db, mock_config.mm_collection)
    assert mock_config.mm_collection in mongo_db.list_collection_names()
    assert mongo_db[mock_config.mm_collection].count_documents({}) == 1
    assert (
        mongo_db[mock_config.mm_collection].find_one().get("current_version")
        == timestamp
    )


def test_set_current_version(mongo_db, mock_config):
    """Test setting the current version."""
    collection_name = mock_config.mm_collection
    create_version_collection(mongo_db, collection_name)
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S%f")
    set_current_version(mongo_db, collection_name, timestamp)
    version = mongo_db[collection_name].find_one().get("current_version")
    assert version == timestamp
