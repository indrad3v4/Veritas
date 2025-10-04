"""
Categorizer Agent - Single Agent for Risk Analysis
WITH COMPREHENSIVE PROMPT LOGGING INCLUDING REASONING CHAIN
"""
import json
import pandas as pd
import io
import time
from typing import Dict, Any
from openai import AsyncOpenAI
from src.Entities import RiskAnalysis, RiskLevel

class CategorizerAgent:
    """
    Single Agent: Risk Analysis & Categorization

    Agent Loop:
    - Instructions: UKNF financial risk analyst
    - Tools: [analyze_risk, detect_anomalies, calculate_scores]
    - Guardrails: Risk score 0-10, confidence 0-1
    - Model: DeepSeek-reasoner (deep reasoning for risk assessment)

    ALL interactions logged INCLUDING THINKING/REASONING CHAIN
    """

    def __init__(self, client: AsyncOpenAI, orchestrator=None):
        self.client = client
        self.orchestrator = orchestrator
        self.model = "deepseek-reasoner"  # Reasoning model for complex analysis

        self.system_instructions = """Jesteś ekspertem analitykiem ryzyka finansowego dla UKNF.

Twoje zadanie:
1. Przeanalizuj dane finansowe z raportu
2. Oceń ryzyko w skali 0-10 (0=bez ryzyka, 10=krytyczne)
3. Zidentyfikuj anomalie i nieprawidłowości
4. Sklasyfikuj raport (płynność/AML/kapitał/governance)
5. Określ pilność (routine/urgent/critical)

KRYTERIA RYZYKA:
- Płynność < 10% aktywów → Ryzyko 8-10 (CRITICAL)
- Płynność 10-20% → Ryzyko 5-7 (URGENT)
- Duże wahania (>50% zmiana M/M) → Ryzyko 6-8
- Brakujące dane → Ryzyko +2
- Transakcje AML >100k EUR bez uzasadnienia → Ryzyko 7-9
- Kapitał < wymogi regulacyjne → Ryzyko 9-10 (CRITICAL)
- Kapitał tuż nad progiem (<5% bufora) → Ryzyko 6-7

ANOMALIE DO WYKRYCIA:
- Outliers (wartości >3 std dev)
- Nagłe zmiany trendu
- Nietypowe wzorce transakcji
- Niezgodności między powiązanymi polami

KLASYFIKACJA:
- liquidity: wskaźniki płynności, LCR, NSFR
- aml: transakcje, PESEL, kwoty, podejrzane operacje
- capital: kapitał, aktywa ważone ryzykiem, współczynniki kapitałowe
- governance: struktura, raporty audytowe, compliance

MYŚL KROK PO KROKU i uzasadnij swoją ocenę szczegółowym łańcuchem rozumowania.

Zwróć JSON:
{
    "category": "liquidity|aml|capital|governance",
    "risk_score": float (0-10),
    "urgency": "routine|urgent|critical",
    "anomalies": ["szczegółowy opis anomalii 1", "anomalia 2"],
    "key_insights": ["kluczowe spostrzeżenie 1", "spostrzeżenie 2"],
    "confidence": float (0-1)
}"""

    async def analyze(self, file_data: bytes, report_type: str) -> RiskAnalysis:
        """
        Run single-agent risk analysis loop WITH REASONING LOGGING

        Agent Flow (with reasoning):
        1. Parse and analyze financial data
        2. Deep reasoning about risk factors (LOGGED)
        3. Calculate risk score with justification
        4. Detect anomalies and patterns
        5. Exit with RiskAnalysis + reasoning chain
        """
        start_time = time.time()

        # Tool: Extract financial data
        try:
            financial_data = await self._extract_financial_data_tool(file_data, report_type)
        except Exception as e:
            fallback = self._create_fallback_analysis(str(e), time.time() - start_time)

            # Log failed extraction
            if self.orchestrator:
                self.orchestrator.log_prompt(
                    agent_name="CategorizerAgent",
                    prompt=f"Extracting financial data for {report_type}",
                    response=f"ERROR: {str(e)}",
                    metadata={
                        "model": self.model,
                        "report_type": report_type,
                        "success": False,
                        "processing_time": time.time() - start_time
                    }
                )

            return fallback

        # Agent deep reasoning prompt
        analysis_prompt = f"""Przeanalizuj raport finansowy:

**Typ raportu:** {report_type}

**Dane finansowe:**
{json.dumps(financial_data, indent=2, ensure_ascii=False)}

**Twoje zadanie:**
Przeprowadź dogłębną analizę ryzyka, odpowiadając na pytania:

1. **Jakie są główne wskaźniki ryzyka w tych danych?**
   - Przeanalizuj kluczowe metryki
   - Porównaj z normami branżowymi
   - Oceń trendy i zmiany

2. **Czy występują anomalie lub nieprawidłowości?**
   - Sprawdź outliers statystyczne
   - Wykryj nietypowe wzorce
   - Zidentyfikuj niezgodności

3. **Jak oceniasz stabilność finansową?**
   - Ocena ogólnej kondycji
   - Identyfikacja zagrożeń
   - Potencjalne scenariusze ryzyka

4. **Jaki poziom pilności wymaga ten raport?**
   - Routine: standardowa analiza, niskie ryzyko
   - Urgent: wymaga szybkiej uwagi, podwyższone ryzyko
   - Critical: natychmiastowa reakcja, wysokie ryzyko

MYŚL KROK PO KROKU i uzasadnij każdą decyzję.

Zwróć szczegółowy JSON z analizą."""

        # Log prompt BEFORE API call
        if self.orchestrator:
            self.orchestrator.log_prompt(
                agent_name="CategorizerAgent",
                prompt=analysis_prompt,
                response="[PENDING DEEP REASONING...]",
                metadata={
                    "model": self.model,
                    "report_type": report_type,
                    "financial_summary": {
                        "rows": financial_data.get("total_rows", 0),
                        "columns": len(financial_data.get("columns", []))
                    },
                    "system_instructions": self.system_instructions[:500] + "..."
                }
            )

        # Call DeepSeek-reasoner (thinking model)
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.system_instructions},
                    {"role": "user", "content": analysis_prompt}
                ],
                temperature=0.3  # Some creativity for risk insights
            )

            # Extract reasoning and final answer
            reasoning_content = getattr(response.choices[0].message, 'reasoning_content', '')
            answer_content = response.choices[0].message.content

            # Log response WITH REASONING CHAIN
            if self.orchestrator:
                self.orchestrator.log_prompt(
                    agent_name="CategorizerAgent",
                    prompt=analysis_prompt,
                    response=f"**REASONING CHAIN:**\n{reasoning_content}\n\n**FINAL ANSWER:**\n{answer_content}",
                    metadata={
                        "model": self.model,
                        "report_type": report_type,
                        "processing_time": time.time() - start_time,
                        "reasoning_length": len(reasoning_content),
                        "success": True,
                        "system_instructions": self.system_instructions[:200] + "..."
                    }
                )

        except Exception as e:
            # Log API failure
            if self.orchestrator:
                self.orchestrator.log_prompt(
                    agent_name="CategorizerAgent",
                    prompt=analysis_prompt,
                    response=f"API ERROR: {str(e)}",
                    metadata={
                        "model": self.model,
                        "report_type": report_type,
                        "processing_time": time.time() - start_time,
                        "success": False
                    }
                )

            return self._create_fallback_analysis(str(e), time.time() - start_time)

        # Parse structured result
        try:
            # Find JSON in the response
            json_start = answer_content.find('{')
            json_end = answer_content.rfind('}') + 1

            if json_start != -1 and json_end != -1:
                json_str = answer_content[json_start:json_end]
                result_data = json.loads(json_str)
            else:
                raise ValueError("No JSON found in response")

        except (json.JSONDecodeError, ValueError) as e:
            return self._create_fallback_analysis(f"JSON parse error: {str(e)}", time.time() - start_time)

        # Map risk score to risk level
        risk_score = result_data.get("risk_score", 5.0)
        if risk_score < 5.0:
            risk_level = RiskLevel.LOW
        elif risk_score < 7.0:
            risk_level = RiskLevel.MEDIUM
        else:
            risk_level = RiskLevel.HIGH

        return RiskAnalysis(
            category=result_data.get("category", report_type),
            risk_score=risk_score,
            risk_level=risk_level,
            urgency=result_data.get("urgency", "routine"),
            anomalies=result_data.get("anomalies", []),
            key_insights=result_data.get("key_insights", []),
            reasoning_chain=reasoning_content or "No reasoning available",
            confidence=result_data.get("confidence", 0.7),
            processing_time=time.time() - start_time,
            agent_model=self.model
        )

    async def _extract_financial_data_tool(self, file_data: bytes, report_type: str) -> Dict[str, Any]:
        """Tool: Extract relevant financial metrics from XLSX"""
        df = pd.read_excel(io.BytesIO(file_data))

        # Basic statistics
        financial_summary = {
            "report_type": report_type,
            "total_rows": len(df),
            "columns": list(df.columns),
            "numeric_columns": df.select_dtypes(include=['number']).columns.tolist(),
            "summary_stats": {}
        }

        # Extract key metrics based on report type
        if report_type in ["liquidity", "płynność"]:
            liquidity_cols = [col for col in df.columns 
                            if any(keyword in col.lower() 
                                  for keyword in ['płyn', 'liquid', 'aktywa', 'assets', 'zobowiązania', 'liabilities'])]
            if liquidity_cols:
                financial_summary["liquidity_data"] = df[liquidity_cols].describe().to_dict()

        elif report_type in ["aml", "anti-money-laundering"]:
            aml_cols = [col for col in df.columns
                       if any(keyword in col.lower()
                             for keyword in ['kwota', 'amount', 'transak', 'transaction', 'pesel'])]
            if aml_cols:
                financial_summary["aml_data"] = df[aml_cols].describe().to_dict()

        elif report_type in ["capital", "kapitał"]:
            capital_cols = [col for col in df.columns
                          if any(keyword in col.lower()
                                for keyword in ['kapitał', 'capital', 'aktywa', 'assets'])]
            if capital_cols:
                financial_summary["capital_data"] = df[capital_cols].describe().to_dict()

        # General numeric summary
        numeric_df = df.select_dtypes(include=['number'])
        if not numeric_df.empty:
            financial_summary["summary_stats"] = numeric_df.describe().to_dict()

        return financial_summary

    def _create_fallback_analysis(self, error_msg: str, processing_time: float) -> RiskAnalysis:
        """Create fallback analysis when agent fails"""
        return RiskAnalysis(
            category="unknown",
            risk_score=5.0,  # Medium risk as fallback
            risk_level=RiskLevel.MEDIUM,
            urgency="routine",
            anomalies=[f"Agent analysis failed: {error_msg}"],
            key_insights=["Wymaga ręcznej weryfikacji przez UKNF"],
            reasoning_chain=f"Agent categorizer failed with error: {error_msg}",
            confidence=0.3,  # Low confidence for fallback
            processing_time=processing_time,
            agent_model=self.model
        )

    async def health_check(self) -> Dict[str, Any]:
        """Test agent connectivity"""
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": "Test analysis: return {\"risk_score\": 2.5, \"category\": \"test\"}"}],
                max_tokens=50
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
