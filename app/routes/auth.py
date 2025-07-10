from fastapi import APIRouter, Response, Cookie
from app.services.oauth_provider import OAuthProviderService
from app.services.oauth import OAuthService
from fastapi import Request
from app.core.database import Database
import time
from app.core.config import Settings
from app.models.user import UserCreate, Abonnement, TypeAbonnement
from fastapi import Depends
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from typing import Annotated, Optional
from app.models.token import TokenData
from datetime import timedelta
from fastapi import HTTPException, status
from app.models.user import User, UserLogin 
import jwt
from jwt.exceptions import InvalidTokenError

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

class AuthRouter():
    def __init__(self):
        self.oauthProvider = OAuthProviderService()
        self.oauth = OAuthService()
        self.router = APIRouter(prefix="/auth", tags=["auth"])
        self._settings = Settings()
        self.db = Database(self._settings)
        self.users_collection = self.db.get_users_collection()

    def get_current_user_dependency(self):
        """Retourne une closure pour la dépendance get_current_user"""
        async def get_current_user(access_token: Optional[str] = Cookie(None)):
            credentials_exception = HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token manquant ou invalide",
                headers={"WWW-Authenticate": "Bearer"},
            )
            
            if not access_token:
                raise credentials_exception
                
            try:
                payload = jwt.decode(access_token, self._settings.SECRET_KEY_JWT, algorithms=[self._settings.ALGORITHM])
                username: str = payload.get("sub")
                if username is None:
                    raise credentials_exception
                token_data = TokenData(username=username)
            except InvalidTokenError:
                raise credentials_exception
            user = self.oauth.get_user(token_data.username)
            if user is None:
                raise credentials_exception
            return user
        return get_current_user
    
    def get_current_active_user_dependency(self):
        """Retourne une closure pour la dépendance get_current_active_user"""
        get_current_user = self.get_current_user_dependency()
        async def get_current_active_user(current_user: Annotated[User, Depends(get_current_user)]):
            if current_user.disabled:
                raise HTTPException(status_code=400, detail="Inactive user")
            return current_user
        return get_current_active_user
    
    def configure_routes(self):
        # Configure les routes dans l'init

        @self.router.get("/login/{provider}")
        async def login_provider(request: Request, provider: str):
            """Redirige l'utilisateur vers le provider pour l'authentification"""
            if not provider:
                return await self.aouth
            return await self.oauthProvider.create_client(provider).authorize_redirect(
                request, 
                "http://localhost:8080/tournaments"
            )

        @self.router.get("/callback/github")
        async def callback_github(request: Request):
            """Récupère le token OAuth et enregistre l'utilisateur dans la base de données"""
            try:
                token = await self.oauthProvider.get_oauth().github.authorize_access_token(request)
                resp = await self.oauthProvider.get_oauth().github.get('user', token=token)
                user_data = resp.json()
            except Exception as e:
                print(f"Erreur OAuth GitHub: {str(e)}")
                raise HTTPException(status_code=400, detail=f"Erreur d'authentification GitHub: {str(e)}")
            
            # Utilise l'email public du profil ou crée un email basé sur le login
            primary_email = user_data.get('email')
            if not primary_email:
                primary_email = f"{user_data['login']}@github.com"
            
            expires_at = int(time.time()) + token.get('expires_in', 3600)
            
            # Vérifie si l'utilisateur existe déjà dans la base de données
            existing_user = self.users_collection.find_one({"provider_id": str(user_data['id'])})
            if not existing_user:
                # Si l'utilisateur n'existe pas, l'enregistre dans la base de données
                self.users_collection.insert_one({
                    "provider": "github",
                    "provider_id": str(user_data['id']),
                    "email": primary_email,
                    "name": user_data.get('name') or user_data['login'],
                    "picture": user_data['avatar_url'],
                    "expires_at": expires_at,
                    "created_at": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
                })
            else:
                # Si l'utilisateur existe déjà, met à jour les champs nécessaires
                self.users_collection.update_one(
                    {"provider_id": str(user_data['id'])},
                    {"$set": {
                        # "access_token": token["access_token"],
                        "updated_at": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
                    }}
                )
            
            user_id = existing_user["_id"] if existing_user else None
            
            # créer une session pour l'utilisateur
            request.session["user_id"] = str(user_id)
            request.session["provider"] = "github"
            request.session["access_token"] = token["access_token"]

            return {"message": "Utilisateur enregistré avec succès",
                    "user": user_data}
        
        @self.router.get("/callback/google")
        async def callback_google(request: Request, response: Response):
            """Récupère le token OAuth et enregistre l'utilisateur dans la base de données"""
            try:
                token = await self.oauthProvider.get_oauth().google.authorize_access_token(request)
                user_info = await self.oauthProvider.get_oauth().google.get("userinfo", token=token)
                user_data = user_info.json()
                expires_at = token["expires_at"]
            except Exception as e:
                print(f"Erreur OAuth Google: {str(e)}")
                raise HTTPException(status_code=400, detail=f"Erreur d'authentification Google: {str(e)}")
            # Vérifie si l'utilisateur existe déjà dans la base de données
            existing_user = self.users_collection.find_one({"provider_id": user_data["id"]})
            if not existing_user:
                # Si l'utilisateur n'existe pas, l'enregistre dans la base de données
                self.users_collection.insert_one({
                    "provider": "google",
                    "provider_id": user_data["id"],
                    "email": user_data["email"],
                    "name": user_data["name"],
                    "picture": user_data["picture"],
                    "expires_at": expires_at,
                    "id_token": token["id_token"],
                    "created_at": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
                })
            else:
                # Si l'utilisateur existe déjà, met à jour les champs nécessaires
                self.users_collection.update_one(
                    {"provider_id": user_data["id"]},
                    {"$set": {
                        # "access_token": token["access_token"],
                        "id_token": token["id_token"],
                        "updated_at": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
                    }}
                )
            user_id = existing_user["_id"] if existing_user else None
            
            # # créer une session pour l'utilisateur
            # request.session["user_id"] = str(user_id)
            # request.session["provider"] = "google"
            # request.session["access_token"] = token["access_token"]
            
            # Définir le cookie sécurisé
            token = self.oauth.create_access_token(
                data={"sub": user_data["email"]}, 
                expires_delta=timedelta(minutes=self._settings.ACCESS_TOKEN_EXPIRE_MINUTES)
            )
            response.set_cookie(
                key="access_token",
                value=token,
                httponly=True,       # Inaccessible depuis JavaScript
                secure=self._settings.is_production,  # Seulement en HTTPS en production
                samesite="strict",   # Protection CSRF
                max_age=self._settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60  # En secondes
            )
            return {"message": "Utilisateur enregistré avec succès",
                    "user": user_data}
        
        @self.router.get("/logout")
        async def logout(request: Request, response: Response):
            """Déconnecte l'utilisateur"""
            user_id = request.session.get("user_id")

            if user_id:
                user = self.users_collection.find_one({"_id": user_id})
                if user and user.access_token:
                    try:
                        if user.provider == "github":
                            await self.oauthProvider.get_oauth().github.revoke(user.access_token)
                        elif user.provider == "google":
                            await self.oauthProvider.get_oauth().google.revoke(user.access_token)
                    except Exception as e:
                        print(f"Erreur lors de la révocation du token: {str(e)}")
                self.users_collection.update_one(
                    {"_id": user_id},
                    {"$set": {
                        # "access_token": None,
                    }}
                )
                request.session.clear()
            
            # Supprimer le cookie d'authentification
            response.delete_cookie(key="access_token")
            return {"message": "Déconnexion réussie"}

        @self.router.post("/logout")
        async def logout_post(response: Response):
            """Déconnecte l'utilisateur (version POST)"""
            # Supprimer le cookie d'authentification
            response.delete_cookie(key="access_token")
            return {"message": "Déconnexion réussie"}

        @self.router.post('/register')
        async def register(user: UserCreate):
            """Enregistre un nouvel utilisateur"""
            return self.oauth.create_user(user)
        
        @self.router.post('/token')
        async def login_for_access_token(
            response: Response, 
            user: UserLogin
        ):
            """Génère un token pour l'utilisateur et l'envoie dans un cookie sécurisé"""
            try:
                user = self.oauth.authenticate_user(user.email, user.password)
            except Exception as e:
                raise HTTPException(status_code=401, detail=f"Invalid username or password: {e}")
            
            access_token_expires = timedelta(minutes=self._settings.ACCESS_TOKEN_EXPIRE_MINUTES)
            access_token = self.oauth.create_access_token(
                data={"sub": user.email}, 
                expires_delta=access_token_expires
            )
            
            # Définir le cookie sécurisé
            response.set_cookie(
                key="access_token",
                value=access_token,
                httponly=True,       # Inaccessible depuis JavaScript
                secure=self._settings.is_production,  # Seulement en HTTPS en production
                samesite="strict",   # Protection CSRF
                max_age=self._settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60  # En secondes
            )
            
            return {"message": "Connexion réussie", "token_type": "bearer"}
        
        @self.router.get("/users/me")
        async def read_users_me(current_user: Annotated[User, Depends(self.get_current_active_user_dependency())]):
            """Récupère les informations de l'utilisateur connecté"""
            return current_user

        @self.router.post("/users/me/abonnement")
        async def update_abonnement(user_id: str, abonnement: Abonnement):
            """Met à jour l'abonnement de l'utilisateur"""
            user = self.users_collection.find_one({"_id": user_id})
            if not user:
                raise HTTPException(status_code=404, detail="User not found")
            user_abonnement = user.abonnement
            if not user_abonnement:
                user_abonnement = Abonnement(
                    type_abonnement=TypeAbonnement.FREE,
                    date_debut=time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
                    date_fin=time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
                    status=True,
                    prix=0
                )
            else:
                user_abonnement.type_abonnement = abonnement.type_abonnement
                user_abonnement.date_debut = abonnement.date_debut
                user_abonnement.date_fin = abonnement.date_fin
                user_abonnement.status = abonnement.status
                user_abonnement.prix = abonnement.prix
            self.users_collection.update_one(
                {"_id": user_id},
                {"$set": {"abonnement": user_abonnement}}
            )
            return user_abonnement
        
        
    def get_router(self):
        self.configure_routes()
        return self.router
