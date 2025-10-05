# Veritas Backend API - Replit Configuration

## Overview

Veritas is an AI-powered communication platform for the Polish Financial Supervision Authority (UKNF) to manage secure, real-time communication with 450+ supervised financial entities. The system uses AI agents to validate financial reports, analyze risk, and generate notifications in Polish.

**Core Purpose:** Automate and streamline the submission, validation, and approval workflow for financial reports between entities (banks, insurance companies) and UKNF supervisors.

**Technology Stack:** FastAPI (Python), DeepSeek AI (3 specialized agents), OpenID Connect authentication, WebSockets for real-time notifications

## Recent Changes

**2025-10-04:** Fixed OIDC callback route to properly handle authentication redirects
- Changed `/api/auth/callback` from POST to GET method
- Fixed query parameter handling (code, state) instead of form data
- Route now correctly handles OIDC provider redirects with query strings
- Resolved LSP type errors in auth.py

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Architectural Pattern: Clean Architecture (4-Layer)

The codebase strictly follows Uncle Bob Martin's Clean Architecture with clear dependency inversion:

1. **Layer 1 - Entities** (`src/Entities/`): Pure domain models with zero external dependencies
   - Business entities: Report, User, Entity, ValidationResult, RiskAnalysis, Notification
   - Business enums: ReportStatus, UserRole, RiskLevel, ReportType, NotificationType
   - **Why:** Isolates core business logic from infrastructure changes

2. **Layer 2 - Use Cases** (`src/UseCases/`): Business logic orchestration
   - Key flows: SubmitReportUseCase, ApproveReportUseCase, RejectReportUseCase, AuthenticateUserUseCase
   - **Why:** Business rules remain testable and independent of frameworks

3. **Layer 3 - Gateways** (`src/Gateways/`): Interface adapters implementing protocols from Use Cases
   - AI Agents: ValidatorAgent, CategorizerAgent, NotifierAgent, AgentOrchestrator
   - Repositories: ReportRepository, UserRepository, EntityRepository (in-memory for demo)
   - Auth: OIDCGateway, JWTValidator
   - Notifications: WebSocketGateway
   - **Why:** Allows swapping implementations without touching business logic

4. **Layer 4 - Externals** (`src/Externals/`): Framework-specific code
   - FastAPI routes: auth, reports, users, entities, health
   - WebSocket handlers
   - Middleware: CORS, logging, error handling
   - **Why:** Framework changes don't cascade into core logic

### AI Agent Architecture: Single-Agent Swarm

**Pattern:** Each agent operates independently with its own instructions, tools, and model selection

**AgentOrchestrator** coordinates three specialized agents:

1. **ValidatorAgent** (DeepSeek-chat)
   - Purpose: Validate XLSX structure and format
   - Tools: parse_excel, validate_columns, check_formats, validate_PESEL
   - Output: ValidationResult with errors/warnings and confidence score
   - **Why DeepSeek-chat:** Fast, accurate for structured validation tasks

2. **CategorizerAgent** (DeepSeek-reasoner)
   - Purpose: Risk analysis and categorization
   - Tools: analyze_risk, detect_anomalies, calculate_scores
   - Output: RiskAnalysis with risk_score (0-10), anomalies, reasoning chain
   - **Why DeepSeek-reasoner:** Deep reasoning capability for complex financial risk assessment

3. **NotifierAgent** (DeepSeek-chat)
   - Purpose: Generate professional Polish notifications
   - Tools: generate_message_pl, format_notification
   - Output: Formatted messages for both entity users and UKNF staff
   - **Why DeepSeek-chat:** Natural language generation with cultural context

**Prompt Logging:** All agent interactions are logged to `prompts.md` for transparency and audit compliance, including full system instructions, user prompts, AI responses, and reasoning chains.

### Authentication & Authorization

**Pattern:** OpenID Connect (OIDC) with JWT session tokens

- **OIDC Flow:** Authorization Code Flow + PKCE for secure external authentication
- **Session Management:** JWT tokens (HS256) stored in HTTP-only cookies
- **Role-Based Access Control:** 3 roles with different permissions
  - ENTITY_OFFICER: Submit reports for assigned entities only
  - UKNF_SUPERVISOR: Review all reports, approve/reject
  - UKNF_ADMIN: User management, system administration

**Implementation:**
- `OIDCGateway`: Handles OIDC provider integration (authorization URL, token exchange)
- `JWTValidator`: Creates and validates internal session JWTs
- `AuthenticateUserUseCase`: Orchestrates OIDC validation and user profile creation

### Real-Time Communication

**Pattern:** WebSocket pub/sub for instant notifications

- **WebSocketGateway:** Manages active connections per user_id
- **ConnectionManager:** Handles connection lifecycle (connect, disconnect, heartbeat)
- **Notification Flow:**
  1. Use Case triggers notification (e.g., report approved)
  2. NotifyUserUseCase creates Notification entity
  3. WebSocketGateway broadcasts to all user connections
  4. Frontend receives JSON message instantly

**Endpoint:** `ws://server/ws?user_id={user_id}`

### Data Persistence Strategy

**Current:** In-memory repositories (demo/prototype mode)
- ReportRepository, UserRepository, EntityRepository use dictionaries
- Seed data for testing: demo entities (mBank, PKO BP, Pekao), demo users

**Production Migration Path:** 
- Repositories already implement async protocols
- Switch to SQLAlchemy + PostgreSQL by implementing same interface
- Zero changes to Use Cases layer (dependency inversion benefit)

**Why this approach:** Rapid prototyping for hackathon, easy migration later without rewriting business logic

### API Design Philosophy

**RESTful endpoints** for CRUD operations:
- `/api/auth/*` - Authentication flow
- `/api/reports/*` - Report submission and review
- `/api/users/*` - User management
- `/api/entities/*` - Entity directory
- `/api/health/*` - System monitoring

**Design decisions:**
- Form data for file uploads (multipart/form-data)
- JSON responses with Pydantic models for type safety
- HTTP status codes follow REST conventions
- Error responses include Polish user-friendly messages

## External Dependencies

### AI & LLM Services

**DeepSeek API** (https://api.deepseek.com)
- Models: deepseek-chat, deepseek-reasoner
- Usage: All 3 AI agents (Validator, Categorizer, Notifier)
- API Key: Required via `DEEPSEEK_API_KEY` environment variable
- Client: OpenAI SDK (AsyncOpenAI) - DeepSeek is OpenAI-compatible

### Authentication Services

**OIDC Provider** (configurable)
- Example: Keycloak realm at `https://auth.veritas-demo.eu/realms/uknf`
- Configuration via environment variables:
  - `OIDC_ISSUER`: Provider URL
  - `OIDC_CLIENT_ID`: OAuth2 client ID
  - `OIDC_CLIENT_SECRET`: OAuth2 client secret
- Library: `authlib` for OIDC flow

### Python Dependencies

**Core Framework:**
- `fastapi==0.104.1` - Web framework
- `uvicorn[standard]==0.24.0` - ASGI server
- `pydantic==2.5.0` - Data validation

**AI Integration:**
- `openai==1.3.7` - DeepSeek API client
- `agents==0.1.0` - Agent framework patterns

**Authentication:**
- `authlib==1.3.0` - OIDC client
- `python-jose[cryptography]==3.3.0` - JWT handling

**Data Processing:**
- `pandas==2.1.4` - XLSX data manipulation
- `openpyxl==3.1.2` - Excel file parsing

**Real-Time:**
- `websockets==12.0` - WebSocket support

**Database (prepared for future):**
- `sqlalchemy==2.0.23` - ORM
- `aiosqlite==0.19.0` - Async SQLite

### Frontend Integration

**Lovable Platform** (https://veritas-uknf.lovable.app)
- Communication: REST API + WebSocket
- CORS configured via `ALLOWED_ORIGINS` environment variable
- Authentication: JWT in HTTP-only cookies with SameSite policy

### Environment Configuration

**Required secrets:**
```
DEEPSEEK_API_KEY=sk-...          # DeepSeek API access
OIDC_ISSUER=https://...          # OIDC provider URL
OIDC_CLIENT_ID=veritas-webapp    # OAuth2 client
OIDC_CLIENT_SECRET=...           # OAuth2 secret
SECRET_KEY=...                   # JWT signing key (32+ chars)
FRONTEND_URL=https://...         # Frontend origin
ALLOWED_ORIGINS=https://...      # CORS whitelist
```

### Deployment Platform

**Replit** (primary deployment target)
- Python 3.11+ runtime
- Port: 5000 (configurable)
- Start command: `uvicorn main:app --host 0.0.0.0 --port 5000`
- File storage: Local filesystem for logs (`prompts.md`)