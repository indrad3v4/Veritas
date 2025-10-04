# Veritas AI Agent Prompt Log

**Purpose:**  
This file logs every prompt and response exchanged between the AgentOrchestrator and the underlying AI agents (Validator, Categorizer, Notifier) as required by UKNF and Clean Architecture transparency. Every prompt design, agent version, user context, processing time, and result is tracked here.

---

## How Orchestrator Logging Works

Every time a user triggers an action that involves an AI agent (report validation, risk analysis, notification), the following information is appended below:

- **Session**: Unique number for each AI interaction.
- **Agent Name**: The agent being used (e.g. ValidatorAgent).
- **Timestamp**: UTC time of invocation.
- **Prompt**: The full prompt sent to the AI model, including context (e.g. data summaries, business rules, error handling instructions).
- **System Instructions**: The full agent instructions defining role and guardrails (e.g. Polish financial compliance specialist, etc.).
- **Metadata**: Model, mode, file size, number of rows, request context.
- **AI Response**: The raw response from DeepSeek (may be truncated if very long).
- **Processing Time**: Time required for the full exchange.
- **Confidence**: If provided, a measure from the AI model (0-1).
- **Success**: Indicates if the agent action succeeded (True/False).

---

## Example Entry

### Session #12: ValidatorAgent
**Timestamp:** 2025-10-04T14:35:21Z  
**Model:** deepseek-chat

**Metadata:**
{
"filename": "liquidity_report_Q3_2025.xlsx",
"file_size": 22380,
"num_rows": 100,
"system_instructions": "Jesteś polskim walidatorem raportów finansowych dla UKNF. Twoje zadanie: 1. Sprawdź strukturę pliku XLSX..."
}

text

**System Instructions:**
Jesteś polskim walidatorem raportów finansowych dla UKNF. Twoje zadanie: 1. Sprawdź strukturę pliku XLSX 2. ...

text

**User Prompt:**
Zwaliduj plik finansowy XLSX (plik: liquidity_report_Q3_2025.xlsx). Kolumny: [Data, Aktywa_Płynne, ...]. ...

text

**AI Response:**
{
"is_valid": true,
"confidence": 0.96,
"errors": [],
"warnings": ["Kolumna 'Uwagi' jest pusta w 3 wierszach"]
}

text

**Analysis:**
- **Tokens (estimated):** ~423 words
- **Processing Time:** 3.2s
- **Confidence:** 0.96
- **Success:** true

---

## Real Log

(Appended by the orchestrator, see AGENT_SWARM.md for design.)

---