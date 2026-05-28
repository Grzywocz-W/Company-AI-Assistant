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
from agents.prompts.prompts import NET_SEARCH_PROMPT
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
        
        self.searchInternet = DuckDuckGoSearchRun()
        
        
        self.tools =[
            Tool(name = "DuckDuckGoSearch",
                 func= self.searchInternet.run,
                 description = "Używaj do przeszukania internetu"
                 ),
            ]
        

        prompt = PromptTemplate.from_template(NET_SEARCH_PROMPT)
        reactAgent = create_react_agent(self.agent, self.tools, prompt)

        self.agentExecutor = AgentExecutor(
            agent = reactAgent,
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

