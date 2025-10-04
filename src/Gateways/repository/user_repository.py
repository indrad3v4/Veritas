"""
User Repository - User data persistence
"""
from typing import Optional, List
from src.Entities import User

class UserRepository:
    """
    In-memory User Repository (Demo)
    In production: Replace with database
    """

    def __init__(self):
        self._users: Dict[str, User] = {}
        self._seed_demo_users()

    def _seed_demo_users(self):
        """Seed demo users for testing"""
        from src.Entities import UserRole

        # Demo Entity User
        entity_user = User(
            id="entity-user-1",
            email="marta.kowalska@mbank.pl",
            name="Marta Kowalska",
            roles=[UserRole.ENTITY_OFFICER],
            entity_access=["MBANK001"],
            entity_names=["mBank S.A."]
        )
        self._users[entity_user.id] = entity_user

        # Demo UKNF Supervisor
        uknf_user = User(
            id="uknf-supervisor-1",
            email="jakub.nowak@uknf.gov.pl",
            name="Jakub Nowak",
            roles=[UserRole.UKNF_SUPERVISOR],
            entity_access=["*"],
            entity_names=["All Entities"]
        )
        self._users[uknf_user.id] = uknf_user

    async def save(self, user: User) -> User:
        """Save or update user"""
        self._users[user.id] = user
        return user

    async def get_by_id(self, user_id: str) -> Optional[User]:
        """Get user by ID"""
        return self._users.get(user_id)

    async def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        for user in self._users.values():
            if user.email == email:
                return user
        return None

    async def get_all(self) -> List[User]:
        """Get all users"""
        return list(self._users.values())
