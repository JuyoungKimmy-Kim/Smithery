import os
from typing import Optional

class Settings:
    # OpenID Connect 설정
    OIDC_CLIENT_ID: str = os.getenv("OIDC_CLIENT_ID", "your_client_id_here")
    OIDC_CLIENT_SECRET: str = os.getenv("OIDC_CLIENT_SECRET", "your_client_secret_here")
    OIDC_DISCOVERY_URL: str = os.getenv("OIDC_DISCOVERY_URL", "https://your-ad-domain.com/.well-known/openid_configuration")
    OIDC_REDIRECT_URI: str = os.getenv("OIDC_REDIRECT_URI", "http://localhost:3000/auth/callback")
    OIDC_SCOPE: str = os.getenv("OIDC_SCOPE", "openid profile email")
    
    # 기존 JWT 설정
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-here")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))
    ALGORITHM: str = "HS256"
    
    # 데이터베이스 설정
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://user:password@localhost/dbname")
    
    # CORS 설정
    ALLOWED_ORIGINS: list = [
        "http://localhost:3000",
        "https://localhost",
        "http://localhost",
        "https://localhost:443",
        "http://localhost:80"
    ]

settings = Settings() 