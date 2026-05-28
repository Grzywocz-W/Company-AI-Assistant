#coordinator.py
import os
import asyncio
###AI
from langchain_google_genai import ChatGoogleGenerativeAI
#from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
#from langchain.agents import AgentExecutor, create_react_agent
from langchain_classic.agents import create_react_agent, AgentExecutor
from langchain_core.prompts import PromptTemplate
from langchain_core.chat_history import InMemoryChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.tools import Tool
####
from models import modelsList
from modelSelector import createLLM
from agents.database_agent import DataBaseAgent
from agents.RAG_agent import RagAgent
from agents.internet_agent import InternetAgent
from reportAgentStatus import AgentStatusAsyncCallbackHandler
from configLoader import loadConfig
from agents.prompts.prompts import COORDINATOR_PROMPT, ADMIN_EXTENSION_PROMPT, QUEST_EXTENSION_PROMPT

api_key = os.getenv("Gemini_API_Key")
backendConfig = loadConfig('config.txt')

#docsPath = "vectorDB"
docsPath=backendConfig.get("VECTOR_DB_PATH")

class CoordinatorAgent:
    def __init__(self, model: modelsList):
        self.model = createLLM(model, temperature=0.0)
        #self.agent = ChatGoogleGenerativeAI(
        #    model=model.value,#jest to enum, a nie tablica
        #    google_api_key=api_key,
        #    temperature=0.0#brak kreatywności. Trzyma się prompta.
        #    )

        #self.chatHistory = []
        #========================AGENCI========================#
        self.dataBaseAgent = DataBaseAgent(model)
        self.ragAgent = RagAgent(model, docsPath)
        self.internetAgent = InternetAgent(model)
        #========================AGENCI========================#

        self.tools =[
            Tool(name = "AgentBazyDanych",
                 func= self.databaseAgent.databaseAgentResponse,
                 description = "Używaj tylko wtedy kiedy otrzymasz zapytanie o przeszukanie bazy danych."
                 ),
            Tool(name = "AgentPrzeszukaniaDokumentów",
                 func= self.ragAgent.ragAgentResponse,
                 description = "Używaj tylko wtedy kiedy otrzymasz zapytanie związane z dokumentacją."
                 ),
            Tool(name = "AgentPrzeszukaniaInternetu",
                 func= self.internetAgent.internetAgentResponse,
                 description = "Używaj do przeszukania sieci. Nie podawaj ŻADNYCH wrażliwych dancyh"
                 ),
            ]
        #dodać później wyszukiwarkę
        prompt = PromptTemplate.from_template(COORDINATOR_PROMPT)
        reactAgent = create_react_agent(self.agent, self.tools, prompt)

        self.agentExecutor = AgentExecutor(
            agent = reactAgent,
            tools = self.tools,
            verbose=True,#wypisuje w konsoli jak myśli
            handle_parsing_errors=True,
            )

        self.chatHistory = InMemoryChatMessageHistory()

        self.agentChat = RunnableWithMessageHistory(
            self.agentExecutor,
            lambda session_id: self.chatHistory,
            input_messages_key="input",
            history_messages_key="history",
        )


    async def coordinatorResponse(self, inputText: str, queue: asyncio.Queue, isAdmin = False):
        #inputMessage = HumanMessage(content=inputText)
        #self.chatHistory.append(inputMessage)
        #response = self.agent.invoke(self.chatHistory)
        #self.chatHistory.append(response)###trzeba dodać!!!!

        self.dataBaseAgent.isAdmin = isAdmin

        if isAdmin:
            promptExtension = ADMIN_EXTENSION_PROMPT
        else:
            promptExtension=QUEST_EXTENSION_PROMPT
        finalInputText = promptExtension + "\n" + inputText
            
        callingListener = AgentStatusAsyncCallbackHandler(queue)
        try:
            response = await self.agentChat.ainvoke(#ainvoke, gdyż asynchroniczne
                {"input": finalInputText},
                config = {
                    "callbacks": [callingListener],
                    "configurable":
                        {"session_id":"local_session"}
                    },
                )
            if isinstance(response, dict):
                return response.get("output", str(response))
            else:
                return str(response)
        
        except Exception as e:
            print(f"[Coordinator]  Błąd koordynatora: {e}")
            return f"Błąd systemu: Koordynator ma problem {e}"


#Odpowiedź z FastAPI: [{"type":"text","text":"Prezydentem Polski jest **Andrzej Duda**.","extras":{"signature":"EjQKMgEMOdbHPsO4j3synvW/fBl9jsvYVahWCk1Vw9y8FyOu9k5VYwixMTnhujLW2eZBV9dF"}}]
#nieaktualne ale on ma cutoff z stycznia 2025 i nie wie o Nawrockim.
