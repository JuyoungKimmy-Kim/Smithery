from authlib.integrations.starlette import OAuth
from authlib.oidc.core import CodeIDToken
from authlib.oidc.core.grants import OpenIDCode
from starlette.requests import Request
from starlette.responses import RedirectResponse
from typing import Optional, Dict, Any
import httpx
import json

from backend.config import settings

class OIDCService:
    def __init__(self):
        self.oauth = OAuth()
        self.oauth.register(
            name='azure_ad',
            client_id=settings.OIDC_CLIENT_ID,
            client_secret=settings.OIDC_CLIENT_SECRET,
            server_metadata_url=settings.OIDC_DISCOVERY_URL,
            client_kwargs={
                'scope': settings.OIDC_SCOPE
            }
        )
    
    async def get_authorization_url(self, request: Request) -> str:
        """OpenID Connect 인증 URL을 생성합니다."""
        redirect_uri = str(request.url_for('oidc_callback'))
        return await self.oauth.azure_ad.authorize_redirect(request, redirect_uri)
    
    async def handle_callback(self, request: Request) -> Dict[str, Any]:
        """OpenID Connect 콜백을 처리합니다."""
        token = await self.oauth.azure_ad.authorize_access_token(request)
        
        # 사용자 정보 가져오기
        user_info = await self.get_user_info(token)
        
        return {
            'token': token,
            'user_info': user_info
        }
    
    async def get_user_info(self, token: Dict[str, Any]) -> Dict[str, Any]:
        """토큰을 사용하여 사용자 정보를 가져옵니다."""
        if 'userinfo' in token:
            return token['userinfo']
        
        # userinfo 엔드포인트가 없는 경우 ID 토큰에서 정보 추출
        if 'id_token' in token:
            id_token = token['id_token']
            # ID 토큰에서 사용자 정보 추출 (실제 구현에서는 JWT 디코딩 필요)
            return {
                'sub': id_token.get('sub'),
                'name': id_token.get('name'),
                'email': id_token.get('email'),
                'preferred_username': id_token.get('preferred_username')
            }
        
        return {}
    
    def get_login_url(self) -> str:
        """로그인 URL을 반환합니다."""
        params = {
            'client_id': settings.OIDC_CLIENT_ID,
            'response_type': 'code',
            'redirect_uri': settings.OIDC_REDIRECT_URI,
            'scope': settings.OIDC_SCOPE,
            'response_mode': 'query'
        }
        
        # discovery URL에서 authorization_endpoint 가져오기
        # 실제 구현에서는 discovery document를 파싱해야 함
        auth_endpoint = f"{settings.OIDC_DISCOVERY_URL.replace('/.well-known/openid_configuration', '')}/oauth2/v2.0/authorize"
        
        query_string = '&'.join([f"{k}={v}" for k, v in params.items()])
        return f"{auth_endpoint}?{query_string}" 