"""
Validator Agent - Single Agent for XLSX Validation
WITH COMPREHENSIVE PROMPT LOGGING
"""
import json
import pandas as pd
import io
import time
from typing import Dict, Any, List
from openai import AsyncOpenAI
from src.Entities import ValidationResult

class ValidatorAgent:
    """
    Single Agent: XLSX File Validation

    Agent Loop:
    - Instructions: Polish financial report validator
    - Tools: [parse_excel, validate_columns, check_formats]
    - Guardrails: Must return valid/invalid + confidence
    - Model: DeepSeek-chat (good for structured validation)

    ALL interactions logged to prompts.md via orchestrator
    """

    def __init__(self, client: AsyncOpenAI, orchestrator=None):
        self.client = client
        self.orchestrator = orchestrator  # For prompt logging
        self.model = "deepseek-chat"

        self.system_instructions = """Jesteś polskim walidatorem raportów finansowych dla UKNF.

Twoje zadanie:
1. Sprawdź strukturę pliku XLSX
2. Zwaliduj wymagane kolumny dla typu raportu
3. Sprawdź poprawność formatów (daty, kwoty, PESEL)
4. Oceń kompletność danych
5. Zwróć wynik walidacji z pewnością 0-1

ZASADY WALIDACJI:
- Raporty płynnościowe: wymagane kolumny [Data, Aktywa_Płynne, Zobowiązania, Wskaźnik_Płynności]
- Raporty AML: wymagane kolumny [PESEL, Kwota, Data_Transakcji, Typ_Operacji]
- Raporty kapitałowe: wymagane kolumny [Data, Kapitał_Własny, Kapitał_Podstawowy, Aktywa_Ważone_Ryzykiem]
- Daty w formacie YYYY-MM-DD lub DD.MM.YYYY
- Kwoty jako liczby (dopuszczalne separatory: . ,)
- PESEL: 11 cyfr z poprawną sumą kontrolną
- Minimalna kompletność: 95% wypełnionych komórek

BŁĘDY KRYTYCZNE (blokują raport):
- Brakujące wymagane kolumny
- Niepoprawny format daty w >10% wierszy
- Ujemne wartości kwotowe (gdzie niedozwolone)
- Niepoprawna suma kontrolna PESEL

OSTRZEŻENIA (nie blokują):
- Brakujące opcjonalne kolumny
- Pojedyncze błędy formatowania (<5% wierszy)
- Nietypowe wartości (outliers)

Odpowiadaj ZAWSZE w JSON:
{
    "is_valid": bool,
    "confidence": float (0-1),
    "errors": [{"column": "nazwa", "row": numer, "issue": "szczegółowy opis"}],
    "warnings": ["ostrzeżenie 1", "ostrzeżenie 2"]
}"""

    async def validate(self, file_data: bytes, filename: str) -> ValidationResult:
        """
        Run single-agent validation loop WITH LOGGING

        Agent Flow:
        1. Parse XLSX file (tool)
        2. Extract data structure
        3. Apply validation rules
        4. Generate structured result
        5. Exit with ValidationResult

        ALL prompts and responses logged via orchestrator
        """
        start_time = time.time()

        # Tool: Parse XLSX
        try:
            parsed_data = await self._parse_excel_tool(file_data)
        except Exception as e:
            error_result = ValidationResult(
                is_valid=False,
                confidence=1.0,
                errors=[{
                    "column": "file",
                    "row": 0,
                    "issue": f"Nie można odczytać pliku XLSX: {str(e)}"
                }],
                processing_time=time.time() - start_time,
                agent_model=self.model
            )

            # Log failed parsing
            if self.orchestrator:
                self.orchestrator.log_prompt(
                    agent_name="ValidatorAgent",
                    prompt=f"Parsing XLSX file: {filename}",
                    response=f"ERROR: {str(e)}",
                    metadata={
                        "filename": filename,
                        "model": self.model,
                        "success": False,
                        "processing_time": time.time() - start_time
                    }
                )

            return error_result

        # Build validation prompt
        validation_prompt = f"""Zwaliduj plik finansowy XLSX:

**Nazwa pliku:** {filename}
**Liczba wierszy:** {parsed_data['rows']}
**Kolumny:** {', '.join(parsed_data['columns'])}

**Typy danych:**
{json.dumps(parsed_data['dtypes'], indent=2, ensure_ascii=False)}

**Braki danych (null counts):**
{json.dumps(parsed_data['null_counts'], indent=2, ensure_ascii=False)}

**Dane przykładowe (pierwsze 5 wierszy):**
{json.dumps(parsed_data['sample_data'], indent=2, ensure_ascii=False)}

Przeprowadź pełną walidację według zasad i zwróć wynik w JSON."""

        # Log prompt BEFORE API call
        if self.orchestrator:
            self.orchestrator.log_prompt(
                agent_name="ValidatorAgent",
                prompt=validation_prompt,
                response="[PENDING...]",
                metadata={
                    "filename": filename,
                    "model": self.model,
                    "file_size": len(file_data),
                    "rows": parsed_data['rows'],
                    "columns": len(parsed_data['columns']),
                    "system_instructions": self.system_instructions[:500] + "..."
                }
            )

        # Call DeepSeek with structured output
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.system_instructions},
                    {"role": "user", "content": validation_prompt}
                ],
                temperature=0.1,  # Low temperature for consistent validation
                response_format={"type": "json_object"}
            )

            response_content = response.choices[0].message.content

            # Log successful response
            if self.orchestrator:
                self.orchestrator.log_prompt(
                    agent_name="ValidatorAgent",
                    prompt=validation_prompt,
                    response=response_content,
                    metadata={
                        "filename": filename,
                        "model": self.model,
                        "processing_time": time.time() - start_time,
                        "success": True,
                        "system_instructions": self.system_instructions[:200] + "..."
                    }
                )

        except Exception as e:
            # Log API failure
            if self.orchestrator:
                self.orchestrator.log_prompt(
                    agent_name="ValidatorAgent",
                    prompt=validation_prompt,
                    response=f"API ERROR: {str(e)}",
                    metadata={
                        "filename": filename,
                        "model": self.model,
                        "processing_time": time.time() - start_time,
                        "success": False
                    }
                )

            return ValidationResult(
                is_valid=False,
                confidence=0.5,
                errors=[{"column": "system", "row": 0, "issue": f"Błąd API: {str(e)}"}],
                processing_time=time.time() - start_time,
                agent_model=self.model
            )

        # Parse agent response
        try:
            result_data = json.loads(response_content)
        except json.JSONDecodeError:
            return ValidationResult(
                is_valid=False,
                confidence=0.5,
                errors=[{"column": "system", "row": 0, "issue": "Błąd parsowania odpowiedzi AI"}],
                processing_time=time.time() - start_time,
                agent_model=self.model
            )

        return ValidationResult(
            is_valid=result_data.get("is_valid", False),
            confidence=result_data.get("confidence", 0.5),
            errors=result_data.get("errors", []),
            warnings=result_data.get("warnings", []),
            processing_time=time.time() - start_time,
            agent_model=self.model
        )

    async def _parse_excel_tool(self, file_data: bytes) -> Dict[str, Any]:
        """Tool: Parse XLSX file and extract structure"""
        try:
            # Read XLSX
            df = pd.read_excel(io.BytesIO(file_data))

            # Extract structure
            return {
                "rows": len(df),
                "columns": list(df.columns),
                "sample_data": df.head(5).fillna("").to_dict(orient="records"),
                "dtypes": {col: str(dtype) for col, dtype in df.dtypes.items()},
                "null_counts": df.isnull().sum().to_dict()
            }
        except Exception as e:
            raise ValueError(f"Cannot parse XLSX: {str(e)}")

    async def health_check(self) -> Dict[str, Any]:
        """Test agent connectivity"""
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": "Test validation: return {\"status\": \"ok\"}"}],
                max_tokens=20,
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
