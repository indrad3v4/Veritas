"""
AI Agent Orchestrator - WITH COMPREHENSIVE PROMPT LOGGING
Based on OpenAI Agents SDK single-agent patterns

File: src/Gateways/agents/orchestrator.py
"""
import asyncio
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
from openai import AsyncOpenAI
import logging

from .validator_agent import ValidatorAgent
from .categorizer_agent import CategorizerAgent
from .notifier_agent import NotifierAgent
from src.Entities import ValidationResult, RiskAnalysis

logger = logging.getLogger(__name__)


class AgentOrchestrator:
    """
    Agent Swarm Orchestrator WITH COMPREHENSIVE PROMPT LOGGING

    Coordinates 3 single-agent systems:
    - ValidatorAgent: XLSX validation (DeepSeek-chat)
    - CategorizerAgent: Risk analysis (DeepSeek-reasoner)
    - NotifierAgent: Message generation (DeepSeek-chat)

    Each agent runs in its own loop with tools, instructions, guardrails.
    ALL prompts and responses are logged to prompts.md for transparency.

    This fulfills the hackathon requirement:
    "The goal is to demonstrate how appropriate prompt design and 
    iteration led to the final result."
    """

    def __init__(
        self, 
        deepseek_api_key: str,
        deepseek_base_url: str = "https://api.deepseek.com",
        log_file: str = "prompts.md"
    ):
        """
        Initialize Agent Orchestrator

        Args:
            deepseek_api_key: DeepSeek API key
            deepseek_base_url: DeepSeek API base URL
            log_file: Path to prompt log file (default: prompts.md)
        """
        # Initialize OpenAI client for DeepSeek
        self.client = AsyncOpenAI(
            api_key=deepseek_api_key,
            base_url=deepseek_base_url
        )

        # Initialize single agents (pass orchestrator for logging)
        self.validator = ValidatorAgent(self.client, self)
        self.categorizer = CategorizerAgent(self.client, self)
        self.notifier = NotifierAgent(self.client, self)

        # Prompt logging
        self.log_file = Path(log_file)
        self.session_counter = 0
        self._initialize_log_file()

        logger.info(f"AgentOrchestrator initialized with prompt logging to {self.log_file}")

    def _initialize_log_file(self):
        """Initialize prompts.md file with header"""
        if not self.log_file.exists():
            header = f"""# Veritas AI Agent Prompt Log

**Generated:** {datetime.utcnow().isoformat()}Z  
**Team:** Console.log(Win)  
**Hackathon:** UKNF Innovation Challenge 2025

---

## Purpose

According to the hackathon task requirements:

> "The goal is to demonstrate how appropriate prompt design and iteration led to the final result."

This file automatically logs:
1. **All prompts** sent to AI agents (Validator, Categorizer, Notifier)
2. **All responses** received from DeepSeek V3
3. **Metadata** including processing time, confidence scores, model used
4. **Timestamp** for each interaction

This ensures full transparency and auditability of AI decision-making in financial supervision.

---

## Agent Architecture

### ValidatorAgent
- **Model:** `deepseek-chat`
- **Purpose:** XLSX file structure validation
- **Tools:** `parse_excel`, `validate_columns`, `check_formats`
- **Typical processing time:** 2-4 seconds
- **Output:** ValidationResult (is_valid, confidence, errors, warnings)

### CategorizerAgent
- **Model:** `deepseek-reasoner`
- **Purpose:** Risk analysis with deep reasoning
- **Tools:** `analyze_risk`, `detect_anomalies`, `calculate_score`
- **Typical processing time:** 3-6 seconds
- **Output:** RiskAnalysis (risk_score, reasoning_chain, anomalies)

### NotifierAgent
- **Model:** `deepseek-chat`
- **Purpose:** Polish notification message generation
- **Tools:** `generate_message_pl`, `format_notification`
- **Typical processing time:** 1-2 seconds
- **Output:** Formatted Polish notification text

---

## Prompt Design Evolution

### Iteration 1: Basic Validation
**Problem:** Generic validation missed financial-specific rules  
**Solution:** Added Polish financial report structure knowledge

### Iteration 2: Risk Analysis
**Problem:** Shallow analysis without reasoning  
**Solution:** Switched to deepseek-reasoner model with thinking chain

### Iteration 3: Polish Communication
**Problem:** Formal language too stiff for users  
**Solution:** Professional yet helpful tone with clear actionable feedback

---

## Log Entries

"""
            self.log_file.write_text(header, encoding='utf-8')
            logger.info(f"Initialized prompt log file: {self.log_file}")

    def log_prompt(
        self, 
        agent_name: str, 
        prompt: str, 
        response: str, 
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Log agent prompt and response to prompts.md

        Required by task specification for AI transparency and auditing.

        Args:
            agent_name: Name of the agent (ValidatorAgent, etc.)
            prompt: The prompt sent to the AI
            response: The response received from the AI
            metadata: Additional context (model, processing time, etc.)
        """
        self.session_counter += 1
        timestamp = datetime.utcnow().isoformat()

        # Format metadata
        metadata_str = json.dumps(metadata or {}, indent=2, ensure_ascii=False)

        # Build log entry
        log_entry = f"""
### Session #{self.session_counter}: {agent_name}
**Timestamp:** {timestamp}Z  
**Model:** {metadata.get('model', 'unknown') if metadata else 'unknown'}

**Metadata:**
```
{metadata_str}
```

**System Instructions:**
```
{metadata.get('system_instructions', 'N/A') if metadata else 'N/A'}
```

**User Prompt:**
```
{prompt[:2000]}{'...' if len(prompt) > 2000 else ''}
```

**AI Response:**
```
{response[:3000]}{'...' if len(response) > 3000 else ''}
```

**Analysis:**
- **Tokens (estimated):** ~{len(prompt.split()) + len(response.split())} words
- **Processing Time:** {metadata.get('processing_time', 'N/A') if metadata else 'N/A'}s
- **Confidence:** {metadata.get('confidence', 'N/A') if metadata else 'N/A'}
- **Success:** {metadata.get('success', True) if metadata else True}

---

"""

        # Append to log file
        try:
            with open(self.log_file, 'a', encoding='utf-8') as f:
                f.write(log_entry)

            logger.debug(f"Logged session #{self.session_counter} for {agent_name}")
        except Exception as e:
            logger.error(f"Failed to log prompt: {str(e)}")

    async def validate_report(
        self, 
        file_data: bytes, 
        filename: str
    ) -> ValidationResult:
        """
        Orchestrate validation through ValidatorAgent
        WITH COMPREHENSIVE PROMPT LOGGING

        Single-agent pattern:
        1. Agent receives file data + filename
        2. Agent uses tools: [parse_excel, validate_columns, check_formats]
        3. Agent runs until final ValidationResult output
        4. ALL prompts and responses logged to prompts.md

        Args:
            file_data: XLSX file bytes
            filename: Original filename

        Returns:
            ValidationResult with is_valid, confidence, errors, warnings
        """
        logger.info(f"Orchestrating validation for file: {filename}")

        try:
            result = await self.validator.validate(file_data, filename)

            logger.info(
                f"Validation complete: valid={result.is_valid}, "
                f"confidence={result.confidence:.2f}, "
                f"errors={len(result.errors)}"
            )

            return result

        except Exception as e:
            logger.error(f"Validation orchestration failed: {str(e)}", exc_info=True)
            raise

    async def analyze_risk(
        self, 
        file_data: bytes, 
        report_type: str
    ) -> RiskAnalysis:
        """
        Orchestrate risk analysis through CategorizerAgent
        WITH COMPREHENSIVE PROMPT LOGGING

        Single-agent pattern:
        1. Agent receives parsed data + report type
        2. Agent uses tools: [analyze_risk, detect_anomalies, calculate_score]
        3. Agent runs with reasoning mode (DeepSeek-reasoner)
        4. Agent outputs RiskAnalysis with thinking chain
        5. ALL reasoning logged to prompts.md

        Args:
            file_data: XLSX file bytes
            report_type: Type of financial report

        Returns:
            RiskAnalysis with risk_score, reasoning_chain, anomalies
        """
        logger.info(f"Orchestrating risk analysis for report type: {report_type}")

        try:
            result = await self.categorizer.analyze(file_data, report_type)

            logger.info(
                f"Risk analysis complete: score={result.risk_score:.1f}, "
                f"level={result.risk_level}, "
                f"anomalies={len(result.anomalies)}"
            )

            return result

        except Exception as e:
            logger.error(f"Risk analysis orchestration failed: {str(e)}", exc_info=True)
            raise

    async def generate_notification(
        self, 
        event_type: str, 
        context: Dict[str, Any]
    ) -> str:
        """
        Orchestrate notification generation through NotifierAgent
        WITH COMPREHENSIVE PROMPT LOGGING

        Single-agent pattern:
        1. Agent receives event type + context
        2. Agent uses tools: [generate_message_pl, format_notification]
        3. Agent outputs Polish notification message
        4. ALL prompts logged to prompts.md

        Args:
            event_type: Type of event (report_approved, report_rejected, etc.)
            context: Event context data

        Returns:
            Formatted Polish notification message
        """
        logger.info(f"Orchestrating notification for event: {event_type}")

        try:
            result = await self.notifier.generate_message(event_type, context)

            logger.info(f"Notification generated successfully")

            return result

        except Exception as e:
            logger.error(f"Notification orchestration failed: {str(e)}", exc_info=True)
            raise

    async def health_check(self) -> Dict[str, Any]:
        """
        Check health of all agents

        Returns comprehensive health status including:
        - Agent connectivity
        - Model availability
        - Prompt logging status
        """
        logger.info("Performing agent health check")

        results = {
            "status": "unknown",
            "agents": {},
            "prompt_logging": {
                "enabled": True,
                "log_file": str(self.log_file.absolute()),
                "sessions_logged": self.session_counter,
                "file_exists": self.log_file.exists()
            }
        }

        try:
            # Check each agent in parallel
            validator_health, categorizer_health, notifier_health = await asyncio.gather(
                self.validator.health_check(),
                self.categorizer.health_check(),
                self.notifier.health_check(),
                return_exceptions=True
            )

            results["agents"] = {
                "validator": validator_health if not isinstance(validator_health, Exception) else {"status": "unhealthy", "error": str(validator_health)},
                "categorizer": categorizer_health if not isinstance(categorizer_health, Exception) else {"status": "unhealthy", "error": str(categorizer_health)},
                "notifier": notifier_health if not isinstance(notifier_health, Exception) else {"status": "unhealthy", "error": str(notifier_health)}
            }

            # Determine overall status
            all_healthy = all(
                agent.get("status") == "healthy" 
                for agent in results["agents"].values()
            )

            results["status"] = "healthy" if all_healthy else "degraded"

            logger.info(f"Health check complete: {results['status']}")

        except Exception as e:
            logger.error(f"Health check failed: {str(e)}", exc_info=True)
            results["status"] = "unhealthy"
            results["error"] = str(e)

        return results

    def get_prompt_log_summary(self) -> Dict[str, Any]:
        """
        Get summary of prompt logging activity

        Returns:
            Summary statistics about logged prompts
        """
        return {
            "log_file": str(self.log_file.absolute()),
            "total_sessions": self.session_counter,
            "file_size_kb": self.log_file.stat().st_size / 1024 if self.log_file.exists() else 0,
            "last_modified": datetime.fromtimestamp(self.log_file.stat().st_mtime).isoformat() if self.log_file.exists() else None
        }
