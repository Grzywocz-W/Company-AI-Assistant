# security_agent.py
import os
import sys
from langchain_classic.agents import create_react_agent, AgentExecutor
from langchain_core.prompts import PromptTemplate
from langchain_core.tools import Tool

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from models import modelsList
from modelSelector import createLLM
from agents.prompts.prompts import SECURITY_PROMPT

api_key = os.getenv("Gemini_API_Key")

class SecurityAgent:

    def __init__(self, model: modelsList):
        # Niska temperatura — agent ma być deterministyczny, nie kreatywny
        self.model = createLLM(model, temperature=0.0)

        #sam agent dokonuje analizy
        def analyzePrompt(text: str):
            #pętla analizy
            return f"Analiza wejścia: {text}"

        self.tools = [
            Tool(
                name="AnalizaBezpieczenstwa",
                func=analyzePrompt,
                description=(
                    "Użyj do przeprowadzenia analizy bezpieczeństwa analizowanego tekstu."
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
            max_iterations=3,  #krótka pętla
        )

    def securityAgentResponse(self, inputText: str):
        try:
            response = self.agentExecutor.invoke(
                {"input": inputText}
                )

            if isinstance(response, dict):
                result = response.get("output", str(response))
            else:
                result = str(response)

            return result

        except Exception as e:
            print(f"[SecurityAgent] Błąd agenta bezpieczeństwa: {e}")
            #jak jest bład to blokujemy
            return f"ZAGROŻENIE: Błąd agenta bezpieczeństwa - {e}"
