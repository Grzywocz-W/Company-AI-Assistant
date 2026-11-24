#internet_agent.py
#ddgs i duckduckgo
import os
import sys
###AI
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_classic.agents import create_react_agent, AgentExecutor
from langchain_core.prompts import PromptTemplate
from langchain_core.chat_history import InMemoryChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.tools import Tool
###internet
from langchain_community.tools import DuckDuckGoSearchRun
from langchain_community.utilities import SearxSearchWrapper
###
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from models import modelsList
from modelSelector import createLLM
from agents.prompts.prompts import NET_SEARCH_PROMPT
from configLoader import loadConfig
backendConfig = loadConfig('config.txt')
#
api_key = os.getenv("Gemini_API_Key")



class InternetAgent:
    def __init__(self, model: modelsList):
        self.model = createLLM(model, temperature=0.3)
##        self.agent = ChatGoogleGenerativeAI(
##            model=model.value,#jest to enum, a nie tablica
##            google_api_key=api_key,
##            temperature=0.3#Wyższa kreatywność
##            )
        
        #self.searchInternet = DuckDuckGoSearchRun()
        self.searxInternet = SearxSearchWrapper(
            searx_host=backendConfig.get("SEARXNG_URL", "http://localhost:8080")  # adres kontenera
        )
        
        self.tools =[
            #Tool(name = "DuckDuckGoSearch",
                 #func= self.searchInternet.run,
                 #description = "Używaj do przeszukania internetu"
                 #),
            Tool(
                name="SearXNGSearch",
                func=self._searchWithSources,
                description="Używaj do przeszukania internetu"
                )
            ]
        

        prompt = PromptTemplate.from_template(NET_SEARCH_PROMPT)
        reactAgent = create_react_agent(self.model, self.tools, prompt)

        self.agentExecutor = AgentExecutor(
            agent = reactAgent,
            tools = self.tools,
            verbose=True,#wypisuje w konsoli jak myśli
            handle_parsing_errors=True,
            )

    def _searchWithSources(self, query: str) -> str:
        results = self.searxInternet.results(query, num_results=5)
        if not results or "Result" in results[0]:
            return "Brak wyników wyszukiwania."

        formatted = []
        for r in results:
            title = r.get("title", "Brak tytułu")
            link = r.get("link", "")
            snippet = r.get("snippet", "")
            formatted.append(f"Tytuł: {title}\nLink: {link}\nOpis: {snippet}")
        return "\n\n".join(formatted)


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
            print(f"[AgentInternetu]  Błąd agenta internetowego: {e}")
            return f"Błąd systemu: Błąd agenta Intenernetu {e}"

