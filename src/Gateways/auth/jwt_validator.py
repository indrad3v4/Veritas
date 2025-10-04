"""
JWT Validator - Internal JWT validation for session tokens
"""
from typing import Dict, Any
from jose import jwt, JWTError
from datetime import datetime, timedelta

class JWTValidator:
    """
    JWT Validator - Validates session JWTs
    """

    def __init__(self, secret_key: str, algorithm: str = "HS256"):
        self.secret_key = secret_key
        self.algorithm = algorithm

    def create_token(self, user_id: str, email: str, roles: list, expires_delta: timedelta = None) -> str:
        """Create JWT token for user session"""
        if expires_delta is None:
            expires_delta = timedelta(hours=24)

        expire = datetime.utcnow() + expires_delta

        payload = {
            "sub": user_id,
            "email": email,
            "roles": roles,
            "exp": expire,
            "iat": datetime.utcnow()
        }

        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)

    def validate_token(self, token: str) -> Dict[str, Any]:
        """Validate JWT token and return claims"""
        try:
            payload = jwt.decode(
                token, 
                self.secret_key, 
                algorithms=[self.algorithm]
            )
            return payload
        except JWTError as e:
            raise ValueError(f"Invalid token: {str(e)}")
