from authlib.integrations.starlette_client import OAuth
from app.core.config import Settings

class OAuthProviderService():
    def __init__(self):
        self._settings = Settings()
        self.oauth = OAuth()
        self.oauth.register(
            name="google",
            client_id=self._settings.GOOGLE_CLIENT_ID,
            client_secret=self._settings.GOOGLE_CLIENT_SECRET,
            authorize_url="https://accounts.google.com/o/oauth2/auth",
            authorize_params={"scope": "openid email profile"},
            access_token_url="https://oauth2.googleapis.com/token",
            client_kwargs={"scope": "openid email profile"},
            api_base_url="https://www.googleapis.com/oauth2/v2/",
            server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
        )
        self.oauth.register(
            name="github",
            client_id=self._settings.GITHUB_CLIENT_ID,
            client_secret=self._settings.GITHUB_CLIENT_SECRET,
            authorize_url="https://github.com/login/oauth/authorize",
            authorize_params={"scope": "user:email read:user"},
            access_token_url="https://github.com/login/oauth/access_token",
            api_base_url="https://api.github.com",
            userinfo_endpoint="https://api.github.com/user",
            client_kwargs={
                "token_endpoint_auth_method": "client_secret_basic",
                "scope": "user:email read:user"
            }
        )
    def get_oauth(self):
        return self.oauth
    
    def create_client(self, provider: str):
        return self.oauth.create_client(provider)