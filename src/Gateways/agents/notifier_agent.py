"""
Notifier Agent - Single Agent for Notification Generation
WITH COMPREHENSIVE PROMPT LOGGING
"""
import json
import time
from typing import Dict, Any
from openai import AsyncOpenAI

class NotifierAgent:
    """
    Single Agent: Notification Message Generation

    Agent Loop:
    - Instructions: Polish communication specialist
    - Tools: [generate_message_pl, format_notification]
    - Guardrails: Professional tone, clear communication
    - Model: DeepSeek-chat

    ALL interactions logged to prompts.md
    """

    def __init__(self, client: AsyncOpenAI, orchestrator=None):
        self.client = client
        self.orchestrator = orchestrator
        self.model = "deepseek-chat"

        self.system_instructions = """Jesteś specjalistą od komunikacji w UKNF (Komisja Nadzoru Finansowego).

Twoje zadanie:
1. Generuj profesjonalne powiadomienia po polsku
2. Dostosuj ton do typu wydarzenia (zatwierdzenie/odrzucenie/błąd)
3. Bądź konkretny i pomocny
4. Używaj języka zrozumiałego dla compliance officers

ZASADY KOMUNIKACJI:
- Zatwierdzenie: ton pozytywny, krótki, informacyjny
  Przykład: "Raport został zatwierdzony. Dziękujemy za terminowe przekazanie danych."

- Odrzucenie: ton profesjonalny, konstruktywna informacja zwrotna
  Przykład: "Raport wymaga poprawy. Proszę sprawdzić uwagi i przesłać ponownie."

- Błąd walidacji: ton pomocny, szczegółowe wskazówki
  Przykład: "Wykryto błędy w strukturze pliku. Zobacz szczegóły i popraw wskazane pozycje."

- Alert systemowy: ton pilny, jasne instrukcje
  Przykład: "Wykryto wysokie ryzyko. Skontaktuj się z zespołem UKNF w ciągu 24h."

DŁUGOŚĆ:
- Tytuł: 40-80 znaków (krótki i konkretny)
- Wiadomość: 150-400 znaków (zwięzła, z konkretnymi informacjami)

STYL:
- Używaj form grzecznościowych: "Proszę", "Dziękujemy"
- Unikaj zbędnego żargonu technicznego
- Podawaj konkretne działania do wykonania
- Zawsze dołączaj kontekst (nazwa raportu, data, itp.)

Zwróć JSON:
{
    "title": "Krótki tytuł powiadomienia",
    "message": "Szczegółowa wiadomość z informacją zwrotną"
}"""

    async def generate_message(
        self, 
        event_type: str, 
        context: Dict[str, Any]
    ) -> str:
        """
        Generate Polish notification message WITH LOGGING

        Agent Flow:
        1. Receive event type + context
        2. Generate appropriate message
        3. Return formatted notification

        ALL prompts logged to prompts.md
        """
        start_time = time.time()

        # Build context-specific prompt
        context_str = "\n".join([f"- **{k}**: {v}" for k, v in context.items()])

        generation_prompt = f"""Wygeneruj powiadomienie dla wydarzenia:

**Typ wydarzenia:** {event_type}

**Kontekst:**
{context_str}

**Wymagania:**
- Tytuł: krótki i konkretny (40-80 znaków)
- Wiadomość: szczegółowa i pomocna (150-400 znaków)
- Ton: dostosowany do typu wydarzenia
- Język: polski, profesjonalny

Zwróć JSON z tytułem i wiadomością."""

        # Log prompt BEFORE API call
        if self.orchestrator:
            self.orchestrator.log_prompt(
                agent_name="NotifierAgent",
                prompt=generation_prompt,
                response="[PENDING...]",
                metadata={
                    "event_type": event_type,
                    "model": self.model,
                    "context_keys": list(context.keys()),
                    "system_instructions": self.system_instructions[:300] + "..."
                }
            )

        # Call DeepSeek
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.system_instructions},
                    {"role": "user", "content": generation_prompt}
                ],
                temperature=0.5,
                response_format={"type": "json_object"}
            )

            response_content = response.choices[0].message.content

            # Log successful response
            if self.orchestrator:
                self.orchestrator.log_prompt(
                    agent_name="NotifierAgent",
                    prompt=generation_prompt,
                    response=response_content,
                    metadata={
                        "event_type": event_type,
                        "model": self.model,
                        "processing_time": time.time() - start_time,
                        "success": True,
                        "system_instructions": self.system_instructions[:200] + "..."
                    }
                )

            return response_content

        except Exception as e:
            # Log API failure
            fallback_message = json.dumps({
                "title": "Powiadomienie systemowe",
                "message": f"Wystąpił błąd podczas generowania powiadomienia: {str(e)}"
            }, ensure_ascii=False)

            if self.orchestrator:
                self.orchestrator.log_prompt(
                    agent_name="NotifierAgent",
                    prompt=generation_prompt,
                    response=f"API ERROR: {str(e)}",
                    metadata={
                        "event_type": event_type,
                        "model": self.model,
                        "processing_time": time.time() - start_time,
                        "success": False
                    }
                )

            return fallback_message

    async def health_check(self) -> Dict[str, Any]:
        """Test agent connectivity"""
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": "Wygeneruj krótkie powiadomienie testowe w JSON"}],
                max_tokens=50,
                response_format={"type": "json_object"}
            )
            return {
                "status": "healthy",
                "model": self.model,
                "response": response.choices[0].message.content.strip()[:100]
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "model": self.model,
                "error": str(e)
            }
