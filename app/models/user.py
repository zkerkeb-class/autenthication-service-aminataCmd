from pydantic import BaseModel
from typing import Optional
from enum import Enum

class TypeAbonnement(str, Enum):
    FREE = 'free'
    PREMIUM = 'premium'
    PRO = 'pro'

class Abonnement(BaseModel):
    type_abonnement: TypeAbonnement
    date_debut: str
    date_fin: str
    status: bool
    prix: float
    created_at: str
    updated_at: Optional[str] = None
    
class User(BaseModel):
    provider: Optional[str] = None
    provider_id: Optional[str] = None
    username: Optional[str] = None
    email: str
    name: Optional[str] = None
    picture: Optional[str] = None
    abonnement: Optional[Abonnement] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

class UserInDB(User):
    password: Optional[str] = None

class UserCreate(BaseModel):
    username: Optional[str] = None
    email: str
    password: str
    name: Optional[str] = None
    picture: Optional[str] = None


class UserLogin(BaseModel):
    email: str
    password: str