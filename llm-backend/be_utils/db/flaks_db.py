from bson.objectid import ObjectId
from flask_pymongo import PyMongo as FlaskPyMongo
from pymongo.collection import Collection
from llm_be_config.configParams import config_params

"""
Hold the database instance (of PyMongo).
Use `from utils.flask_db import db` then db() to get access to the instance,
or use 'collection(<name>)' to get a specific collection (i.e. collection('tests')).
"""

_db = None


def db():
    """
    get the db instance
    """
    global _db
    return _db


class Collections:
    @staticmethod
    def by_name(collection_name):
        """Return a collection by the given name

        :param str collection_name:
        :rtype: Collection
        """
        return db().db[collection_name]


def register_mongo(app):
    global _db
    _db = FlaskPyMongo(app)
    return db()


def as_object_id(doc_id):
    return doc_id if isinstance(doc_id, ObjectId) else ObjectId(doc_id)

