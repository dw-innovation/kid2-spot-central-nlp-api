import unittest
import os
from dotenv import load_dotenv
from pymongo import MongoClient

"""
Test module for basic MongoDB operations using unittest.

To run:
    python -m unittest tests.test_mongodb_ops
"""

load_dotenv()

MONGO_DB_URL = os.getenv('MONGO_URI')
client = MongoClient(MONGO_DB_URL)
db = client['test_database']


class TestMongoDB(unittest.TestCase):
    """
    Unit tests for MongoDB CRUD operations on a test collection.
    """
    def test_insert(self):
        """
        Test that a document can be inserted into the MongoDB collection.

        Verifies:
            - `insert_one` returns an object with a valid inserted_id.
        """
        # Test insert operation
        collection = db['test_collection']
        result = collection.insert_one({'name': 'John', 'age': 30})
        self.assertIsNotNone(result.inserted_id)

    def test_find(self):
        """
        Test that a previously inserted document can be found in the collection.

        Assumes:
            - A document with {'name': 'John', 'age': 30} was previously inserted.

        Verifies:
            - `find_one` returns a non-None result.
            - The returned document has the expected 'age' value.
        """
        # Test find operation
        collection = db['test_collection']
        result = collection.find_one({'name': 'John'})
        self.assertIsNotNone(result)
        self.assertEqual(result['age'], 30)

    # Add more test cases for other MongoDB operations as needed


if __name__ == '__main__':
    unittest.main()
