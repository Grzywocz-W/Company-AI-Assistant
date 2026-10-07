# security_agent.py
import os
from langchain_classic.agents import create_react_agent, AgentExecutor
from langchain_core.prompts import PromptTemplate
from langchain_core.tools import Tool

from models import modelsList
from modelSelector import createLLM
from agents.prompts.prompts import SECURITY_PROMPT

api_key = os.getenv("Gemini_API_Key")

class SecurityAgent:
    """
    Agent do spraw bezpieczeństwa.
    Analizuje potencjalnie złośliwe prompty zanim trafia do dalszego
    przetwarzania (SQL injection, prompt injection, próby zmiany roli, itp.)
    Zwraca: "BEZPIECZNY" albo "ZAGROŻENIE: <opis>"
    """

    def __init__(self, model: modelsList):
        # Niska temperatura — agent ma być deterministyczny, nie kreatywny
        self.model = createLLM(model, temperature=0.0)

        # Agent bezpieczeństwa nie potrzebuje zewnętrznych narzędzi —
        # całą analizę przeprowadza sam model na podstawie promptu systemowego.
        # Dodajemy jedno wewnętrzne "pseudo-narzędzie" analizy,
        # które zamyka wzorzec ReAct w sensownej pętli.
        def analyzePrompt(text: str) -> str:
            """
            Wewnętrzne narzędzie — zwraca wynik analizy bezpieczeństwa
            fragmentu tekstu przekazanego przez koordynatora.
            """
            # Faktyczna analiza odbywa się przez LLM w pętli ReAct,
            # to narzędzie służy jako punkt wejścia do wzorca.
            return f"Analiza wejścia: {text}"

        self.tools = [
            Tool(
                name="AnalizaBezpieczenstwa",
                func=analyzePrompt,
                description=(
                    "Użyj do przeprowadzenia szczegółowej analizy bezpieczeństwa podanego tekstu."
                ),
            )
        ]

        prompt = PromptTemplate.from_template(SECURITY_PROMPT)
        reactAgent = create_react_agent(self.model, self.tools, prompt)

        self.agentExecutor = AgentExecutor(
            agent=reactAgent,
            tools=self.tools,
            verbose=True,
            handle_parsing_errors=True,
            max_iterations=3,  # Celowo krótka pętla — decyzja powinna być szybka
        )

    def securityAgentResponse(self, inputText: str) -> str:
        """
        Główna metoda.
        Przyjmuje podejrzany prompt od koordynatora.
        Zwraca string: "BEZPIECZNY" albo "ZAGROŻENIE: <opis>"
        """
        try:
            response = self.agentExecutor.invoke({"input": inputText})

            if isinstance(response, dict):
                result = response.get("output", str(response))
            else:
                result = str(response)

            return result

        except Exception as e:
            print(f"[SecurityAgent] Błąd agenta bezpieczeństwa: {e}")
            # W razie wątpliwości — blokujemy. Fail-safe.
            return f"ZAGROŻENIE: Błąd wewnętrzny agenta bezpieczeństwa — {e}"