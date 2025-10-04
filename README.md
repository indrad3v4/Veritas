# 🏛️ Veritas Backend API

**AI-Powered Communication Platform for UKNF**  
Team: Console.log(Win) | Hackathon: UKNF Innovation Challenge 2025

---

## Overview

A backend for secure, real-time communication between the Polish Financial Supervision Authority (UKNF) and 450+ supervised entities.  
🏗 Built using Clean Architecture with FastAPI, DeepSeek AI Agents, OIDC authentication, and WebSockets.

## Key Features

- **ValidatorAgent:** AI-validation of XLSX reports; structured feedback, error/warning tags, confidence scores.
- **CategorizerAgent:** AI-driven risk scoring using financial reasoning and transparent chains.
- **NotifierAgent:** Polish notifications generated for both compliance officers and UKNF staff.
- **Prompt Logging:** All agent interactions are audited in `prompts.md` (see there for format).
- **Clean Architecture:** Each layer (Entities → UseCases → Gateways → Externals) is clearly separated.
- **Replit + Lovable integration:** One-click deployment to Replit and easy Lovable frontend consumption.

## Quick Start

Clone project...
git clone https://github.com/your-org/veritas-backend.git
cd veritas-backend

Install dependencies...
pip install -r requirements.txt

Configure environment...
cp .env.example .env

Edit .env (see below)
Run the server...
uvicorn main:app --host 0.0.0.0 --port 8000 --reload

text

## Environment (.env)

DEEPSEEK_API_KEY=sk-your-deepseek-api-key
OIDC_ISSUER=https://auth.veritas-demo.eu/realms/uknf
OIDC_CLIENT_ID=veritas-webapp
OIDC_CLIENT_SECRET=your-client-secret
SECRET_KEY=your-very-long-random-string
FRONTEND_URL=https://veritas-uknf.lovable.app
ALLOWED_ORIGINS=https://veritas-uknf.lovable.app

text

## File Structure

veritas/
├── docs/ # Documentation for agents, API, architecture, deployment
├── src/ # All backend code (Clean Architecture)
├── main.py # FastAPI entry point
├── prompts.md # ALL AI agent prompts and responses (see above)
├── README.md # This file!
├── requirements.txt
└── tests/

text

## Key Endpoints

| Route                            | Method | Description                  |
|-----------------------------------|--------|------------------------------|
| /api/reports                     | POST   | Submit XLSX report           |
| /api/reports                     | GET    | List reports                 |
| /api/reports/{id}                | GET    | Report details, AI analysis  |
| /api/reports/{id}/approve        | POST   | Approve (UKNF)               |
| /api/reports/{id}/reject         | POST   | Reject (UKNF)                |
| /api/entities                    | GET    | Entity directory             |
| /api/auth/login                  | GET    | OIDC: Start login flow       |
| /api/auth/callback               | POST   | OIDC: Finish login           |
| /ws?user_id={id}                 | WS     | Real-time notifications      |
| /api/health                      | GET    | Health checks                |

See `docs/API.md` for full specs and payloads.

## Prompt Logging & AI Transparency

- Every prompt + response (and result, errors, confidence, tokens, and reasoning chain) is auto-logged to `prompts.md` in Markdown+JSON.
- See examples in `prompts.md`.
- Designed to meet UKNF and hackathon transparency criteria.

## Testing

pytest tests/

text

## Team

- **@indra_dev4** - Backend/AI/architecture
- **@czdream** - Code/infra/clean arch
- **@maryna_zhk** - Frontend/Lovable/UX

---

MIT License – UKNF Innovation Challenge, 2025

**Console.log("README gotowy! Happy hacking and AI supervision! 🚀")**
