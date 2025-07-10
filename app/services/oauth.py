from app.core.config import Settings
from passlib.context import CryptContext
from app.core.database import Database
from app.models.user import UserInDB
from datetime import datetime, timedelta, timezone
import jwt
from fastapi import HTTPException
from app.models.user import UserCreate

class OAuthService():
    def __init__(self):
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        self.settings = Settings()
        self.db = Database(self.settings)
        self.users_collection = self.db.get_users_collection()
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        return self.pwd_context.verify(plain_password, hashed_password)
    
    def get_password_hash(self, password: str) -> str:
        return self.pwd_context.hash(password)
    
    def get_user(self, email: str) -> UserInDB | None:
        user = self.users_collection.find_one({"email": email})
        if user:
            return UserInDB(**user)
        return None
    
    def authenticate_user(self, email: str, password: str) -> UserInDB:
        user = self.get_user(email)
        if not user:
            return False
        if not self.verify_password(password, user.password):
            return False
        return user
    
    def create_access_token(self, data: dict, expires_delta: timedelta = None):
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + timedelta(minutes=15)
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, self.settings.SECRET_KEY_JWT, algorithm=self.settings.ALGORITHM)
        return encoded_jwt
    
    def create_user(self, user: UserCreate):
        if self.users_collection.find_one({"email": user.email}):
            raise HTTPException(status_code=400, detail="Email already exists")
        hashed_password = self.get_password_hash(user.password)
        userDump = user.model_dump()
        userDump["password"] = hashed_password
        result = self.users_collection.insert_one(userDump)
        created_user = self.users_collection.find_one({"_id": result.inserted_id})

        if created_user and "_id" in created_user:
            created_user["_id"] = str(created_user["_id"])
        return created_user