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
#
api_key = os.getenv("Gemini_API_Key")



class InternetAgent:
    def __init__(self, model: modelsList):
        
        self.agent = ChatGoogleGenerativeAI(
            model=model.value,#jest to enum, a nie tablica
            google_api_key=api_key,
            temperature=0.3#Wyższa kreatywność
            )
        
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
        

        ZASADY:
        1. ZAWSZE używaj narzędzia DuckDuckGosEARCH.
        2. Jako argumenty narzędzia DuckDuckGosEARCH, podawaj krótkie frazy.
        3. Swoją odpowiedź opieraj tylko na dancyh zwróconych z narzędzia.
        4. Masz zwrócić najważniejsze wydobyte informacje, nie cały tekst.
        5. Przpomnij, że informacje znalezione w Internecie nie zawsze są prawdziwe
        
        Narzędzia: {tools}
        
        Format:
        Question: Rozkaz od Koordynatora
        Thought: Musisz przeszukać Internet.
        Action: {tool_names}
        Action Input: <szukanie frazy>
        Observation: Wyniki z sieci.
        Thought: Masz potrzebne dane. Sformułuj raport.
        Final Answer: Raport dla Koordynatora.

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
        response = self.agentExecutor.invoke(
            {"input": inputText}
            )
        

        ###odpowiedź zawiera też podpis(signature)
        #response = response.content#wydobywamy tylko zawartość
        try:
            return response.get("output", "Błąd")#wydobywany pole text(niżej)
        except (IndexError, KeyError, TypeError):
            return str(response)

        return str(response)

