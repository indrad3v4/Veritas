# Veritas Clean Architecture Documentation

**File:** `docs/ARCHITECTURE.md`  
**Team:** Console.log(Win)  
**Pattern:** Clean Architecture (Uncle Bob Martin)

---

## Architecture Overview

Veritas follows **Clean Architecture** principles with **4 distinct layers** that enforce dependency inversion and business logic isolation.

```
🔴 Layer 4: EXTERNALS (Frameworks & Drivers)
    ↑ depends on
🟡 Layer 3: GATEWAYS (Interface Adapters) 
    ↑ depends on
🔵 Layer 2: USE CASES (Business Rules)
    ↑ depends on
🟢 Layer 1: ENTITIES (Domain Models)
```

## Layer Breakdown

### 🟢 Layer 1: ENTITIES (Domain Models)
**Location:** `src/Entities/`  
**Purpose:** Pure business entities with zero external dependencies  
**Rules:** Cannot import from other layers

```python
# Pure domain models
- Report (core business entity)
- User (authentication & authorization)  
- ValidationResult (AI validation output)
- RiskAnalysis (AI risk assessment)
- Entity (financial institution)
- Enums (business value objects)
```

**Key Principles:**
```python
class Report(BaseModel):
    # Business rules embedded in domain
    def is_high_risk(self) -> bool:
        return self.risk_score > 7.0

    def requires_escalation(self) -> bool:
        return self.is_high_risk() or len(self.anomalies) >= 3
```

### 🔵 Layer 2: USE CASES (Business Logic)
**Location:** `src/UseCases/`  
**Purpose:** Orchestrate business rules, independent of external systems  
**Dependencies:** Only Entities layer

```python
# Business logic orchestration
- SubmitReportUseCase (core workflow)
- ApproveReportUseCase (UKNF decision)
- RejectReportUseCase (UKNF feedback)
- GetReportsUseCase (role-based access)
- AuthenticateUserUseCase (OIDC integration)
- NotifyUserUseCase (real-time communication)
```

**Dependency Inversion Example:**
```python
class SubmitReportUseCase:
    def __init__(
        self,
        validator_agent: ValidatorAgentProtocol,  # Interface
        categorizer_agent: CategorizerAgentProtocol,  # Interface
        report_repository: ReportRepositoryProtocol,  # Interface
        notification_gateway: NotificationGatewayProtocol  # Interface
    ):
        # Use Cases depend on abstractions, not concretions
```

### 🟡 Layer 3: GATEWAYS (Interface Adapters)
**Location:** `src/Gateways/`  
**Purpose:** Implement external system interfaces  
**Dependencies:** Entities + UseCases (interfaces only)

```python
# Interface implementations
auth/
├── OIDCGateway (implements authentication)
├── JWTValidator (implements token validation)

agents/
├── AgentOrchestrator (coordinates AI agents)
├── ValidatorAgent (implements validation)
├── CategorizerAgent (implements risk analysis)
├── NotifierAgent (implements communication)

repository/
├── ReportRepository (implements data persistence)
├── UserRepository (implements user storage)
├── EntityRepository (implements entity data)

notifications/
├── WebSocketGateway (implements real-time messaging)
```

**Gateway Implementation Pattern:**
```python
class ValidatorAgent(ValidatorAgentProtocol):
    """Implements validation interface for Use Cases"""

    async def validate(self, file_data: bytes, filename: str) -> ValidationResult:
        # External DeepSeek API integration
        # Returns pure domain entity (ValidationResult)
```

### 🔴 Layer 4: EXTERNALS (Frameworks & Drivers)
**Location:** `src/Externals/`  
**Purpose:** Framework-specific implementations  
**Dependencies:** All layers (orchestrates everything)

```python
api/
├── routes/ (FastAPI REST endpoints)
├── middleware.py (CORS, error handling)
├── dependencies.py (dependency injection)

websocket/
├── connection_manager.py (WebSocket handling)
├── handlers.py (real-time endpoints)

database/
├── connection.py (database setup)
├── models.py (ORM models)

frontend/
├── API_SPEC.md (integration docs)
├── .env.example (frontend config)
```

## Dependency Flow

```
FastAPI Route → Use Case → Gateway → External System
     ↓             ↓         ↓           ↓
  External    Business   Interface   Framework
   Layer      Logic      Adapter     Driver
```

**Example Request Flow:**
```python
1. POST /api/reports (FastAPI route)
   ↓
2. SubmitReportUseCase.execute() (business logic)
   ↓
3. ValidatorAgent.validate() (gateway to AI)
   ↓
4. DeepSeek API call (external system)
   ↓
5. ValidationResult (domain entity)
   ↓ 
6. JSON response (FastAPI serialization)
```

## Key Benefits

### 1. **Testability**
```python
# Use Cases testable with mocks
def test_submit_report():
    mock_validator = MockValidatorAgent()
    mock_repository = MockReportRepository()

    use_case = SubmitReportUseCase(
        validator_agent=mock_validator,
        report_repository=mock_repository
    )

    result = await use_case.execute(user, entity, report_type, file_data)
    assert result.is_valid
```

### 2. **Framework Independence**
```python
# Business logic independent of FastAPI
# Could switch to Django/Flask without changing Use Cases
# AI agents could switch from DeepSeek to OpenAI without changing business logic
```

### 3. **Database Independence**
```python
# Repository pattern abstracts database
# Could switch from SQLite to PostgreSQL without changing Use Cases
# In-memory repositories for testing
```

### 4. **UI Independence**
```python
# Same backend serves:
- REST API (for Lovable frontend)
- WebSocket (for real-time updates)
- Future: GraphQL, CLI, mobile app
```

## Design Patterns Used

### 1. **Repository Pattern**
```python
class ReportRepositoryProtocol(Protocol):
    async def save(self, report: Report) -> Report: ...
    async def get_by_id(self, report_id: str) -> Report | None: ...

class SQLReportRepository(ReportRepositoryProtocol):
    # SQL implementation

class InMemoryReportRepository(ReportRepositoryProtocol):
    # In-memory implementation for testing
```

### 2. **Dependency Injection**
```python
# FastAPI dependencies.py
def get_submit_report_use_case(
    orchestrator: AgentOrchestrator = Depends(get_agent_orchestrator),
    report_repo: ReportRepository = Depends(get_report_repository)
) -> SubmitReportUseCase:
    return SubmitReportUseCase(
        validator_agent=orchestrator.validator,
        report_repository=report_repo
    )
```

### 3. **Factory Pattern**
```python
class AgentOrchestrator:
    def __init__(self, api_key: str):
        self.client = AsyncOpenAI(api_key=api_key)
        self.validator = ValidatorAgent(self.client)
        self.categorizer = CategorizerAgent(self.client)
```

### 4. **Observer Pattern**
```python
# WebSocket notifications as observers
class NotifyUserUseCase:
    async def notify_report_approved(self, report: Report):
        # Notify via WebSocket
        # Notify via email (future)
        # Log notification (audit)
```

## File Organization

```
src/
├── Entities/           # 🟢 Layer 1: Pure domain
│   ├── report.py
│   ├── user.py
│   └── enums.py
│
├── UseCases/          # 🔵 Layer 2: Business logic  
│   ├── submit_report.py
│   ├── approve_report.py
│   └── authenticate_user.py
│
├── Gateways/          # 🟡 Layer 3: Interfaces
│   ├── agents/
│   ├── auth/
│   ├── repository/
│   └── notifications/
│
└── Externals/         # 🔴 Layer 4: Frameworks
    ├── api/
    ├── websocket/
    ├── database/
    └── frontend/
```

## Testing Strategy

### Unit Tests
```python
# Test Entities (business rules)
def test_report_is_high_risk():
    report = Report(risk_score=8.5)
    assert report.is_high_risk() == True

# Test Use Cases (business logic)
def test_submit_report_use_case():
    # Mock all gateways
    # Test business logic in isolation
```

### Integration Tests  
```python
# Test Gateways (external integrations)
def test_validator_agent():
    # Test actual DeepSeek API integration
    # Verify ValidationResult structure

# Test API Routes (full stack)
def test_submit_report_endpoint():
    # Test FastAPI route with test client
    # Verify HTTP responses
```

## Production Considerations

### Scalability
```python
# Horizontal scaling
- Multiple FastAPI instances
- Load balancer for API requests
- Agent pool for AI processing
- Database connection pooling
```

### Monitoring
```python
# Observability at each layer
- API metrics (FastAPI)
- Business metrics (Use Cases)
- Integration metrics (Gateways)
- Infrastructure metrics (Database, AI APIs)
```

### Security
```python
# Security boundaries
- API authentication (OIDC)
- Business authorization (Use Cases)
- Data validation (Entities)
- External API security (Gateways)
```

---

## Summary

Veritas Clean Architecture provides:

✅ **Separation of Concerns** - Each layer has single responsibility  
✅ **Dependency Inversion** - High-level modules don't depend on low-level  
✅ **Testability** - Business logic testable in isolation  
✅ **Flexibility** - Easy to swap implementations  
✅ **Maintainability** - Clear structure and boundaries  

**Console.log("Clean Architecture documentation готов! Solid foundation for UKNF hackathon scalability. 🏗️"); ✅**