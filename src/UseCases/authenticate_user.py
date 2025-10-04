"""
Authenticate User Use Case - OIDC integration
"""
from typing import Protocol, Dict, Any
from src.Entities import User, UserRole

class OIDCGatewayProtocol(Protocol):
    async def validate_token(self, token: str) -> Dict[str, Any]: ...

class UserRepositoryProtocol(Protocol):
    async def get_by_email(self, email: str) -> User | None: ...
    async def save(self, user: User) -> User: ...

class AuthenticateUserUseCase:
    """
    Business Logic: Authenticate user via OIDC and create/update profile

    Business Rules:
    - Valid OIDC token required
    - Extract roles from JWT claims
    - Create user if doesn't exist
    - Update existing user profile
    """

    def __init__(
        self,
        oidc_gateway: OIDCGatewayProtocol,
        user_repository: UserRepositoryProtocol
    ):
        self.oidc = oidc_gateway
        self.repository = user_repository

    async def execute(self, oidc_token: str) -> User:
        """Authenticate user and return user profile"""

        # Step 1: Validate OIDC token
        try:
            claims = await self.oidc.validate_token(oidc_token)
        except Exception as e:
            raise ValueError(f"Invalid OIDC token: {str(e)}")

        # Step 2: Extract user info from claims
        email = claims.get("email")
        name = claims.get("name") or claims.get("given_name", "") + " " + claims.get("family_name", "")
        roles_claim = claims.get("roles", [])
        entity_access = claims.get("entity_access", [])
        entity_names = claims.get("entity_names", [])

        if not email:
            raise ValueError("Email not found in OIDC token")

        # Step 3: Convert roles to UserRole enums
        user_roles = []
        for role_str in roles_claim:
            try:
                user_roles.append(UserRole(role_str))
            except ValueError:
                pass  # Skip invalid roles

        if not user_roles:
            raise ValueError("No valid roles found in OIDC token")

        # Step 4: Get or create user
        existing_user = await self.repository.get_by_email(email)

        if existing_user:
            # Update existing user
            existing_user.name = name
            existing_user.roles = user_roles
            existing_user.entity_access = entity_access
            existing_user.entity_names = entity_names
            existing_user.is_active = True
            return await self.repository.save(existing_user)
        else:
            # Create new user
            new_user = User(
                id=claims.get("sub") or email,  # Use 'sub' claim or email as ID
                email=email,
                name=name,
                roles=user_roles,
                entity_access=entity_access,
                entity_names=entity_names
            )
            return await self.repository.save(new_user)
