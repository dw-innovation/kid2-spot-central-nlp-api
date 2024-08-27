import unittest
import os
from dotenv import load_dotenv
from pymongo import MongoClient

'''
Run python -m unittest tests.test_mongodb_ops
'''

load_dotenv()

MONGO_DB_URL = os.getenv('MONGO_URI')
client = MongoClient(MONGO_DB_URL)
db = client['test_database']


class TestMongoDB(unittest.TestCase):

    def test_insert(self):
        # Test insert operation
        collection = db['test_collection']
        result = collection.insert_one({'name': 'John', 'age': 30})
        self.assertIsNotNone(result.inserted_id)

    def test_find(self):
        # Test find operation
        collection = db['test_collection']
        result = collection.find_one({'name': 'John'})
        self.assertIsNotNone(result)
        self.assertEqual(result['age'], 30)

    # Add more test cases for other MongoDB operations as needed


if __name__ == '__main__':
    unittest.main()
