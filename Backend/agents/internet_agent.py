#internet_agent.py.py
#ddgs i duckduckgo
import os
###AI
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_classic.agents import create_react_agent, AgentExecutor
from langchain_core.prompts import PromptTemplate
from langchain_core.chat_history import InMemoryChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.tools import Tool
###internet
from langchain_community.tools import DuckDuckGoSearchRun
###
from models import modelsList
from modelSelector import createLLM
#
api_key = os.getenv("Gemini_API_Key")



class InternetAgent:
    def __init__(self, model: modelsList):
        self.agent = createLLM(model, temperature=0.3)
##        self.agent = ChatGoogleGenerativeAI(
##            model=model.value,#jest to enum, a nie tablica
##            google_api_key=api_key,
##            temperature=0.3#Wyższa kreatywność
##            )
        
        self.searchInternet = DuckDuckGoSearchRun()
        
        
        self.tools =[
            Tool(name = "DuckDuckGosEARCH",
                 func= self.searchInternet.run,
                 description = "Używaj do przeszukania internetu"
                 ),
            ]
        

        
        systemPrompt = """
        Jesteś agentem ds. wyszukiwania informacji w Internecie.
        Otrzymujesz polecenie od Koordynatora. Masz za zadanie przeszukać sieć i zwrócić najważniejsze informacje.
        

        ZASADY BEZPIECZEŃSTWA I REALIZACJI ZADAŃ (GUARDRAILS):
        1. ZAWSZE używaj narzędzia DuckDuckGosEARCH. Masz ZAKAZ korzystania ze swojej wiedzy.
        2. Jako argumenty narzędzia DuckDuckGosEARCH, podawaj krótkie frazy.
        3. Nie odpowiadaj na tematy: nielegalne, skrajnie drastyczne, zachęcające do przemocy oraz zakaz pozyskiwania wrażliwych danych osobowych. W takich przypadkach natychmiast przerwij działanie
        3. Swoją odpowiedź opieraj tylko na dancyh zwróconych z narzędzia.
        4. Masz zwrócić najważniejsze wydobyte informacje, nie kopiuj całego tekstu.
        5. Na końcu informacji (Final Answer) przpomnij, że informacje znalezione w Internecie nie zawsze są prawdziwe
        
        Narzędzia: {tools}
        
        Format:
        Question: Rozkaz od Koordynatora
        Thought: Przygotowanie słów kluczowych do przeszukania internetu.
        Action: {tool_names}
        Action Input: <szukanie frazy>
        Observation: Wyniki z sieci.
        Thought: Wydobycie najważniejszych danych i sformułowanie raportu.
        Final Answer: Raport dla Koordynatora oraz załączenie klauzuli o ostrożności..

        Question: {input}
        Thought:{agent_scratchpad}
        """

        prompt = PromptTemplate.from_template(systemPrompt)
        agentTMP = create_react_agent(self.agent, self.tools, prompt)

        self.agentExecutor = AgentExecutor(
            agent = agentTMP,
            tools = self.tools,
            verbose=True,#wypisuje w konsoli jak myśli
            handle_parsing_errors=True,
            )


    def internetAgentResponse(self, inputText: str):

        try:
            response = self.agentExecutor.invoke(
                {"input": inputText}
                )
            if isinstance(response, dict):
                return response.get("output", str(response))
            else:
                return str(response)
        

        ###odpowiedź zawiera też podpis(signature)
        #response = response.content#wydobywamy tylko zawartość
        except Exception as e:
            print(f"[AgentInternetu]  Błąd agenta Intenernetu: {e}")
            return f"Błąd systemu:Błąd agenta Intenernetu {e}"

