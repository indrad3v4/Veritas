"""
Entity Repository - Entity data persistence
"""
from typing import Optional, List
from src.Entities import Entity

class EntityRepository:
    """
    In-memory Entity Repository (Demo)
    """

    def __init__(self):
        self._entities: Dict[str, Entity] = {}
        self._seed_demo_entities()

    def _seed_demo_entities(self):
        """Seed demo entities for testing"""
        entities = [
            Entity(
                code="MBANK001",
                name="mBank S.A.",
                short_name="mBank",
                nip="5260250995",
                krs="0000025237",
                lei="254900GDZFHF2T298714",
                entity_type="bank",
                total_reports=45,
                approved_reports=42,
                average_risk_score=3.2
            ),
            Entity(
                code="PKOBP001",
                name="Powszechna Kasa Oszczędności Bank Polski S.A.",
                short_name="PKO BP",
                nip="5252842728",
                krs="0000026438",
                lei="259400R9L8QEF85K8M19",
                entity_type="bank",
                total_reports=67,
                approved_reports=65,
                average_risk_score=2.8
            ),
            Entity(
                code="PEKAO001",
                name="Bank Pekao S.A.",
                short_name="Pekao",
                nip="5260210708",
                krs="0000014843",
                lei="259400R9LE46TQMVZ326",
                entity_type="bank",
                total_reports=52,
                approved_reports=50,
                average_risk_score=3.0
            )
        ]

        for entity in entities:
            self._entities[entity.code] = entity

    async def save(self, entity: Entity) -> Entity:
        """Save or update entity"""
        self._entities[entity.code] = entity
        return entity

    async def get_by_code(self, code: str) -> Optional[Entity]:
        """Get entity by code"""
        return self._entities.get(code)

    async def get_all(self) -> List[Entity]:
        """Get all entities"""
        return list(self._entities.values())
