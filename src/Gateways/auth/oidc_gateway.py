"""
OIDC Gateway - OpenID Connect Authentication
"""
import secrets
import hashlib
import base64
from typing import Dict, Any
from authlib.integrations.httpx_client import AsyncOAuth2Client
from authlib.jose import jwt
import httpx

class OIDCGateway:
    """
    OpenID Connect Gateway - Handles OIDC authentication flow

    Implements Authorization Code Flow + PKCE
    """

    def __init__(self, issuer: str, client_id: str, client_secret: str):
        self.issuer = issuer
        self.client_id = client_id
        self.client_secret = client_secret
        self.discovery_url = f"{issuer}/.well-known/openid-configuration"
        self._metadata = None

    async def get_metadata(self) -> Dict[str, Any]:
        """Get OIDC provider metadata"""
        if self._metadata is None:
            async with httpx.AsyncClient() as client:
                response = await client.get(self.discovery_url)
                response.raise_for_status()
                self._metadata = response.json()
        return self._metadata

    def generate_pkce_challenge(self) -> Dict[str, str]:
        """Generate PKCE code verifier and challenge"""
        code_verifier = base64.urlsafe_b64encode(secrets.token_bytes(32)).decode('utf-8').rstrip('=')
        code_challenge = base64.urlsafe_b64encode(
            hashlib.sha256(code_verifier.encode('utf-8')).digest()
        ).decode('utf-8').rstrip('=')

        return {
            "code_verifier": code_verifier,
            "code_challenge": code_challenge,
            "code_challenge_method": "S256"
        }

    async def get_authorization_url(self, redirect_uri: str) -> str:
        """Generate OIDC authorization URL"""
        metadata = await self.get_metadata()
        pkce = self.generate_pkce_challenge()
        state = secrets.token_urlsafe(32)

        auth_endpoint = metadata["authorization_endpoint"]

        params = {
            "client_id": self.client_id,
            "response_type": "code",
            "scope": "openid profile email",
            "redirect_uri": redirect_uri,
            "state": state,
            "code_challenge": pkce["code_challenge"],
            "code_challenge_method": pkce["code_challenge_method"]
        }

        query_string = "&".join([f"{k}={v}" for k, v in params.items()])
        return f"{auth_endpoint}?{query_string}"

    async def exchange_code_for_tokens(
        self, 
        code: str, 
        code_verifier: str, 
        redirect_uri: str
    ) -> Dict[str, str]:
        """Exchange authorization code for tokens"""
        metadata = await self.get_metadata()
        token_endpoint = metadata["token_endpoint"]

        async with httpx.AsyncClient() as client:
            response = await client.post(
                token_endpoint,
                data={
                    "grant_type": "authorization_code",
                    "code": code,
                    "redirect_uri": redirect_uri,
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "code_verifier": code_verifier
                }
            )
            response.raise_for_status()
            return response.json()

    async def validate_token(self, token: str) -> Dict[str, Any]:
        """Validate ID token and extract claims"""
        metadata = await self.get_metadata()
        jwks_uri = metadata["jwks_uri"]

        # Fetch JWKS
        async with httpx.AsyncClient() as client:
            response = await client.get(jwks_uri)
            response.raise_for_status()
            jwks = response.json()

        # Decode and validate JWT
        claims = jwt.decode(token, jwks)
        claims.validate()

        return claims
