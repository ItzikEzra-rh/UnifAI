from datetime import datetime
from be_utils.db.flaks_db import *


class HFTokenManager:
    # Class variable to hold the token
    _token = None

    def __init__(self, collection_name='huggingFaceTokens'):
        self.collection = Collections.by_name(collection_name)

    def save_token(self, token):
        # Save the token in MongoDB with a timestamp
        token_data = {
            "token": token,
            "created_at": datetime.utcnow()
        }
        self.collection.insert_one(token_data)
        HFTokenManager._token = token

    def retrieve_token(self):
        # Retrieve the latest token from MongoDB
        latest_token_entry = self.collection.find_one(
            sort=[("created_at", -1)]
        )
        if latest_token_entry:
            HFTokenManager._token = latest_token_entry['token']
        return HFTokenManager._token
