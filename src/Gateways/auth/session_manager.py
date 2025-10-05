
"""
Session Manager - Temporary storage for OIDC flow state
"""
from typing import Dict, Optional
from datetime import datetime, timedelta
import secrets

class SessionManager:
    """In-memory session storage for OIDC authentication flow"""
    
    def __init__(self, ttl_minutes: int = 10):
        self._sessions: Dict[str, Dict] = {}
        self.ttl = timedelta(minutes=ttl_minutes)
    
    def create_session(self, state: str, code_verifier: str, redirect_uri: str) -> None:
        """Store OIDC session data"""
        self._sessions[state] = {
            "code_verifier": code_verifier,
            "redirect_uri": redirect_uri,
            "created_at": datetime.utcnow()
        }
        self._cleanup_expired()
    
    def get_session(self, state: str) -> Optional[Dict]:
        """Retrieve session data by state token"""
        self._cleanup_expired()
        return self._sessions.get(state)
    
    def delete_session(self, state: str) -> None:
        """Remove session after use"""
        self._sessions.pop(state, None)
    
    def _cleanup_expired(self) -> None:
        """Remove expired sessions"""
        now = datetime.utcnow()
        expired = [
            state for state, data in self._sessions.items()
            if now - data["created_at"] > self.ttl
        ]
        for state in expired:
            del self._sessions[state]
