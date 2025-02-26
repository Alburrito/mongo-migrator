import time
from pymongo import MongoClient

def setup_test_db():
    # Connect to MongoDB container using the connection string
    print("Connecting to MongoDB...")
    client = MongoClient("mongodb://root:rootpassword@localhost:27017/")
    
    # Wait for MongoDB to start
    print("Waiting for MongoDB to start...")
    time.sleep(5)
    
    # Create a database called 'test-db'
    db = client['test-db']
    print("Database 'test-db' created.")
    
    # Create a collection called 'test-collection'
    collection = db['test-collection']
    print("Collection 'test-collection' created.")
    
    # Add some example documents to the collection
    documents = [
        {"name": "Document 1", "value": 1},
        {"name": "Document 2", "value": 2}
    ]
    collection.insert_many(documents)
    print("Documents inserted into 'test-collection'.")

    # Check that the documents were inserted
    print("Inserted documents:")
    for doc in collection.find():
        print(doc)

    # Close the connection to MongoDB
    client.close()

if __name__ == "__main__":
    setup_test_db()
