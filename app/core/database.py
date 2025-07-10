from pymongo import MongoClient
from app.core.config import Settings

class Database:
    def __init__(self, settings: Settings):
        self.client = MongoClient(settings.MONGODB_URI)
        self.db = self.client["volleyball-db-local"]
        self.users_collection = self.db["users"]

    def get_db(self):
        return self.db
    
    def get_users_collection(self):
        return self.users_collection