# Veritas Deployment Guide

**File:** `docs/DEPLOYMENT.md`  
**Team:** Console.log(Win)  
**Target Platforms:** Replit (Backend) + Lovable (Frontend)

---

## Deployment Overview

Veritas uses a **split deployment strategy**:
- **Backend API:** Deployed on Replit for easy Python hosting
- **Frontend App:** Deployed on Lovable for rapid UI development
- **Communication:** REST API + WebSocket between platforms

## Backend Deployment (Replit)

### 1. **Replit Setup**

#### Create New Repl
```bash
# 1. Go to https://replit.com
# 2. Click "Create Repl"
# 3. Choose "Python" template
# 4. Name: "veritas-backend"
# 5. Import from GitHub (optional)
```

#### Project Structure
```
veritas/
├── main.py                 # FastAPI entry point
├── requirements.txt        # Python dependencies  
├── .env                   # Environment variables
├── src/                   # Application code
├── tests/                 # Test suite
└── README.md              # Setup instructions
```

### 2. **Environment Configuration**

#### `.env` File (Replit Secrets)
```bash
# Add these in Replit Secrets tab
DEEPSEEK_API_KEY=sk-your-deepseek-api-key-here
OIDC_ISSUER=https://auth.veritas-demo.eu/realms/uknf
OIDC_CLIENT_ID=veritas-webapp
OIDC_CLIENT_SECRET=your-oidc-secret
FRONTEND_URL=https://veritas-uknf.lovable.app
SECRET_KEY=your-jwt-secret-key-32-chars-min
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=1440
DATABASE_URL=sqlite:///./veritas_demo.db
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=INFO
ALLOWED_ORIGINS=https://veritas-uknf.lovable.app,https://veritas-uknf-{user}.lovable.app
```

#### Replit Configuration Files

**`.replit`**
```toml
[nix]
channel = "stable-24.05"

[deployment]
run = ["python", "main.py"]
deploymentTarget = "cloudrun"

[[ports]]
localPort = 8000
externalPort = 80
```

**`replit.nix`**
```nix
{ pkgs }: {
  deps = [
    pkgs.python311
    pkgs.python311Packages.pip
    pkgs.python311Packages.fastapi
    pkgs.python311Packages.uvicorn
  ];
}
```

**`pyproject.toml`**
```toml
[tool.poetry]
name = "veritas-backend"
version = "1.0.0"
description = "AI-powered UKNF communication platform"

[tool.poetry.dependencies]
python = "^3.11"
fastapi = "^0.104.1"
uvicorn = {extras = ["standard"], version = "^0.24.0"}
pydantic = "^2.5.0"
authlib = "^1.3.0"
python-jose = {extras = ["cryptography"], version = "^3.3.0"}
openai = "^1.3.7"
pandas = "^2.1.4"
openpyxl = "^3.1.2"
websockets = "^12.0"
sqlalchemy = "^2.0.23"
aiosqlite = "^0.19.0"
httpx = "^0.25.2"
python-multipart = "^0.0.6"
```

### 3. **Deployment Steps**

#### Step 1: Upload Code
```bash
# Option A: Upload files directly to Replit
# - Drag & drop project folder
# - Or use Replit Git integration

# Option B: Clone from GitHub
git clone https://github.com/your-username/veritas-backend.git
cd veritas-backend
```

#### Step 2: Install Dependencies
```bash
# Replit automatically installs from requirements.txt
# Or manually install:
pip install -r requirements.txt
```

#### Step 3: Configure Environment
```bash
# In Replit Secrets tab, add all environment variables
# Or create .env file (not recommended for production)
```

#### Step 4: Run Application
```bash
# Click "Run" button in Replit, or:
python main.py

# Verify startup:
# ✅ Veritas Backend API started successfully!
# 📡 REST API: https://veritas-backend.your-username.repl.co/docs
# 🔌 WebSocket: wss://veritas-backend.your-username.repl.co/ws
```

### 4. **Replit URLs**

Your deployed backend will be available at:
```
Main API: https://veritas-backend.{username}.repl.co
API Docs: https://veritas-backend.{username}.repl.co/docs
Health: https://veritas-backend.{username}.repl.co/api/health
WebSocket: wss://veritas-backend.{username}.repl.co/ws
```

### 5. **Database Setup**

#### SQLite (Default for Demo)
```python
# Database auto-initializes on first run
# File location: /app/veritas_demo.db
# Demo data seeded automatically
```

#### Production Database (Future)
```bash
# For production, replace with PostgreSQL
DATABASE_URL=postgresql://user:password@host:port/database
```

## Frontend Deployment (Lovable)

### 1. **Lovable Setup**

#### Create New Project
```bash
# 1. Go to https://lovable.dev
# 2. Click "Create New Project"
# 3. Choose "React TypeScript" template
# 4. Name: "veritas-frontend"
# 5. Select deployment region (Europe for UKNF)
```

#### Environment Variables (Lovable)
```bash
# Add in Lovable environment settings
VITE_API_BASE_URL=https://veritas-backend.{username}.repl.co
VITE_WS_URL=wss://veritas-backend.{username}.repl.co/ws
VITE_ENVIRONMENT=production
VITE_OIDC_CLIENT_ID=veritas-webapp
VITE_OIDC_REDIRECT_URI=https://veritas-uknf.lovable.app/auth/callback
```

### 2. **Frontend Integration Code**

#### API Client Setup
```typescript
// src/lib/api.ts
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

export class VeritasAPI {
  private baseURL: string;

  constructor() {
    this.baseURL = API_BASE_URL;
  }

  async submitReport(entityCode: string, reportType: string, file: File) {
    const formData = new FormData();
    formData.append('entity_code', entityCode);
    formData.append('report_type', reportType);
    formData.append('file', file);

    const response = await fetch(`${this.baseURL}/api/reports`, {
      method: 'POST',
      body: formData,
      credentials: 'include'
    });

    return response.json();
  }

  async getReports(status?: string) {
    const params = new URLSearchParams();
    if (status) params.append('status', status);

    const response = await fetch(`${this.baseURL}/api/reports?${params}`, {
      credentials: 'include'
    });

    return response.json();
  }
}
```

#### WebSocket Integration
```typescript
// src/lib/websocket.ts
export class VeritasWebSocket {
  private ws: WebSocket | null = null;
  private userId: string;

  constructor(userId: string) {
    this.userId = userId;
  }

  connect() {
    const wsUrl = `${import.meta.env.VITE_WS_URL}?user_id=${this.userId}`;
    this.ws = new WebSocket(wsUrl);

    this.ws.onmessage = (event) => {
      const data = JSON.parse(event.data);

      if (data.type === 'notification') {
        // Show toast notification
        this.showNotification(data.data);
      }
    };
  }

  private showNotification(notification: any) {
    // Integrate with your notification system
    console.log('New notification:', notification);
  }
}
```

### 3. **Lovable Deployment**

#### Automatic Deployment
```bash
# Lovable automatically deploys on code changes
# Build process:
# 1. npm install
# 2. npm run build  
# 3. Deploy to CDN
# 4. Update URL: https://veritas-uknf.lovable.app
```

#### Custom Domain (Optional)
```bash
# Configure custom domain in Lovable settings:
# veritas.uknf.gov.pl → https://veritas-uknf.lovable.app
```

## Integration Testing

### 1. **End-to-End Testing**

#### Test Backend Endpoints
```bash
# Test API health
curl https://veritas-backend.{username}.repl.co/api/health

# Expected response:
{
  "status": "healthy",
  "service": "Veritas Backend API",
  "version": "1.0.0"
}
```

#### Test WebSocket Connection
```javascript
// Browser console test
const ws = new WebSocket('wss://veritas-backend.{username}.repl.co/ws?user_id=test');
ws.onopen = () => console.log('Connected');
ws.onmessage = (e) => console.log('Message:', e.data);
```

#### Test CORS Integration
```javascript
// Frontend should be able to make API calls
fetch('https://veritas-backend.{username}.repl.co/api/health', {
  credentials: 'include'
})
.then(r => r.json())
.then(console.log);
```

### 2. **Production Readiness Checklist**

#### Backend (Replit)
```bash
✅ Environment variables configured
✅ HTTPS enabled (automatic in Replit)
✅ CORS configured for Lovable domain
✅ Database initialized with demo data
✅ AI agents health check passing
✅ WebSocket endpoints working
✅ Error handling and logging configured
```

#### Frontend (Lovable)  
```bash
✅ API base URL pointing to Replit
✅ WebSocket URL configured
✅ OIDC redirect URLs match
✅ Build optimization enabled
✅ Environment variables set
✅ Error boundaries implemented
```

#### Integration
```bash
✅ API calls work from frontend to backend
✅ WebSocket notifications received
✅ File upload functionality working
✅ Authentication flow complete
✅ Real-time updates functional
```

## Monitoring & Maintenance

### 1. **Health Monitoring**

#### Backend Health Checks
```bash
# Automated monitoring URLs
GET https://veritas-backend.{username}.repl.co/api/health
GET https://veritas-backend.{username}.repl.co/api/health/agents
GET https://veritas-backend.{username}.repl.co/api/health/detailed
```

#### Frontend Health
```bash
# Lovable provides built-in monitoring
# Check deployment status in Lovable dashboard
```

### 2. **Log Monitoring**

#### Backend Logs (Replit)
```bash
# View logs in Replit console
# Key metrics to monitor:
- API request/response times
- AI agent success rates  
- Database query performance
- WebSocket connection count
- Error rates by endpoint
```

#### AI Prompt Logs
```bash
# All AI interactions logged to prompts.md
# Monitor for:
- Agent response quality
- Processing times
- Error rates
- Token usage/costs
```

### 3. **Scaling Considerations**

#### Replit Limitations
```bash
# Current limitations:
- Single instance deployment
- Limited concurrent connections (~100)
- Memory limit ~1GB
- No load balancing

# Scale-up options:
- Replit Teams for more resources
- Deploy to Railway/Render for production
- Use Kubernetes for enterprise scale
```

#### Production Migration Path
```bash
# Future production deployment:
Backend: AWS ECS + RDS PostgreSQL + ElastiCache
Frontend: Vercel/Netlify + CDN
Database: AWS RDS PostgreSQL
AI: DeepSeek API + Azure OpenAI fallback
Monitoring: DataDog/New Relic
```

## Deployment URLs Summary

### Development
```bash
Backend: https://veritas-backend.{username}.repl.co
Frontend: https://veritas-uknf.{user}.lovable.app
```

### Production (Demo)
```bash
Backend: https://veritas-backend-official.repl.co  
Frontend: https://veritas-uknf.lovable.app
WebSocket: wss://veritas-backend-official.repl.co/ws
API Docs: https://veritas-backend-official.repl.co/docs
```

### UKNF Integration (Future)
```bash
Backend: https://api.veritas.uknf.gov.pl
Frontend: https://veritas.uknf.gov.pl
```

---

## Quick Deployment Commands

### Backend (Replit)
```bash
# 1. Create Replit → Python template
# 2. Upload code or clone from GitHub
# 3. Add environment variables in Secrets
# 4. Click "Run" → Backend ready!
```

### Frontend (Lovable)  
```bash
# 1. Create Lovable project → React TypeScript
# 2. Set environment variables (VITE_API_BASE_URL)
# 3. Build components using Lovable AI
# 4. Deploy automatically → Frontend ready!
```

### Integration Test
```bash
curl https://veritas-backend.{username}.repl.co/api/health
# + Open https://veritas-uknf.lovable.app
# + Test file upload → Verify backend communication
```

**Console.log("Deployment documentation готов! Replit + Lovable integration guide complete. Ready for UKNF demo! 🚀"); ✅**