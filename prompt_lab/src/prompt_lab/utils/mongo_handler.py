# from bson.objectid import ObjectId
# from pymongo import MongoClient
# from config.configParams import config_params
# from be_utils.utils import shell_exec
# import os
# import functools
# import logging
# import json
#
# """
# Hold the database instance (of PyMongo).
# Use `from utils.db import db` then db() to get access to the instance,
# or use 'collection(<name>)' to get a specific collection (i.e. collection('tests')).
# """
#
# _db = None
#
#
# def db():
#     """
#     get the db instance
#     """
#     global _db
#     return _db
#
#
# class Collections(object):
#
#     @staticmethod
#     def by_name(collection_name):
#         """Return a collection by the given name
#
#         :param str collection_name:
#         :rtype: Collection
#         """
#         return db()[collection_name]
#
#
# def dump_documents(collection_name, query, output, gzip=True):
#     """
#     dumping documents from collection by query and export to json file
#     :param collection_name: collection to export from
#     :param query: query of the documents to export
#     :param output: output destination - output is from json format
#     :return: dump path
#     """
#
#     command = f"""mongodump {'--gzip' if gzip else ''} --uri="{config_params.MONGODB_URL}" -d={config_params.MONGODB_BACKEND_COLLECTION} -c={collection_name} -q={query} --out={output}"""
#     rc, stdout = shell_exec(command)
#     if rc == 0:
#         return True
#     else:
#         raise Exception(f'mongodump failed: {stdout}')
#
#
# def restore_documents(collection_name,
#                       bson_to_restore_path,
#                       index_restore=False,
#                       maintain_insertion_order=True,
#                       drop=True,
#                       gzip=True):
#     """
#     restoring documents from bson file
#     :param collection_name:
#     :param bson_to_restore_path:
#     :param index_restore:
#     :param maintain_insertion_order:
#     :param drop:
#     :param gzip:
#     :return:
#     """
#     params = ['--noIndexRestore' if not index_restore else '',
#               '--maintainInsertionOrder' if maintain_insertion_order else '',
#               '--drop' if drop else '']
#     command = f"""mongorestore  {'--gzip' if gzip else ''} --uri="{config_params.MONGODB_URL}" -d={config_params.MONGODB_BACKEND_COLLECTION}  --collection={collection_name} {' '.join(params)} {bson_to_restore_path}"""
#     logging.info(command)
#     rc, stdout = shell_exec(command)
#     if rc == 0:
#         return True
#     else:
#         raise Exception(f'mongorestore failed: {stdout}')
#
#
# def register_mongo():
#     global _db
#
#     if not os.environ.get("MONGO_ENV", None):
#         db_location = os.path.join(config_params.MONGODB_URL, config_params.MONGODB_BACKEND_COLLECTION)
#     else:
#         db_location = os.path.join(os.environ.get("MONGO_ENV"), config_params.MONGODB_BACKEND_COLLECTION)
#     db_name = db_location.split('/')
#     _db = MongoClient(db_location)[db_name[len(db_name) - 1]]
#     return db()
#
#
# def as_objectId(doc_id):
#     return doc_id if isinstance(doc_id, ObjectId) else ObjectId(doc_id)
#
#
# def mongo(task):
#     @functools.wraps(task)
#     def _task(*args, **kwargs):
#         register_mongo()
#         return task(*args, **kwargs)
#
#     return _task
