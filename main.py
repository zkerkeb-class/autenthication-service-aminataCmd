from fastapi import FastAPI
from app.routes.auth import AuthRouter
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from app.core.config import Settings

app = FastAPI()

auth_router = AuthRouter()
settings = Settings()

app.add_middleware(SessionMiddleware, 
                    secret_key=settings.SECRET_KEY,
                    same_site="lax",  # Permet les redirections OAuth
                    https_only=settings.is_production)

app.add_middleware(CORSMiddleware, 
                    allow_origins=["http://localhost:8080", "https://your-frontend-domain.com"],
                    allow_credentials=True, 
                    allow_methods=["GET", "POST", "PUT", "DELETE"], 
                    allow_headers=["Content-Type", "Authorization", "X-CSRF-Token"])
app.include_router(auth_router.get_router())

@app.get("/", tags=["root"])
async def root():
    return {"message": "Bienvenue sur l'API Auth avec Oauth2"}

