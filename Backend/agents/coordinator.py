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


api_key = os.getenv("Gemini_API_Key")

docsPath = "vectorDB"

class CoordinatorAgent:
    def __init__(self, model: modelsList):
        self.agent = createLLM(model, temperature=0.0)
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
                 func= self.dataBaseAgent.dataBaseAgentResponse,
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

        systemPrompt = """Jesteś Koordynatorem systemu AI, która ma odpowiadać na pytanie użytkowników zwiazanych z zadaniami. Też pomagasz administatorowi w jego pracy. 
        Twoim JEDYNYM zadaniem jest przekierowywanie zapytań do innych agentów lub wywoływanie innych narzędzi.
        
        Najważniejsze zasady
        1. NIE odpowiadaj na pytania nie związane z pomocą użytkownikowi. Musi to być związane z istotą systemu.
        2. UŻYWAJ innych agentów aby rozwiązywać problem.
        3. Odpowiedź na użytkownika musi być zwięzłym przekazaniem wiedzy pozyskanej z narzędzi/agentów.

        Dostępne narzędzia i agenci:
        {tools}
        
        Używaj poniższego formatu:
        Question: Pytanie, na które masz odpowiedzieć.
        Thought: Myśl, co masz zrobić, jakich narzędzi użyć itp.
        Action: Specjalistów wybieraj tylko z {tool_names}
        Action Input: Wywołanie odpowiedniego specjalisty
        Observation: Wynik akcji
        Thought: Otrzymałeś raport i go analizujesz.
        Final Answer: [Podsumowanie oparte TYLKO I WYŁĄCZNIE na raporcie z kroku Observation]

        Historia konwersacji:
        {history}

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

        self.chatHistory = InMemoryChatMessageHistory()

        self.agentChat = RunnableWithMessageHistory(
            self.agentExecutor,
            lambda session_id: self.chatHistory,
            input_messages_key="input",
            history_messages_key="history",
        )


    async def coordinatorResponse(self, inputText: str, queue: asyncio.Queue):
        #inputMessage = HumanMessage(content=inputText)
        #self.chatHistory.append(inputMessage)
        #response = self.agent.invoke(self.chatHistory)
        #self.chatHistory.append(response)###trzeba dodać!!!!
        callingListener = AgentStatusAsyncCallbackHandler(queue)
        
        response = await self.agentChat.ainvoke(#ainvoke, gdyż asynchroniczne
            {"input": inputText},
            config = {
                "callbacks": [callingListener],
                "configurable":
                    {"session_id":"local_session"}
                },
            )
        

        ###odpowiedź zawiera też podpis(signature)
        #response = response.content#wydobywamy tylko zawartość
        try:
            return response.get("output", "Błąd")#wydobywany pole text(niżej)
        except (IndexError, KeyError, TypeError):
            return str(response)

        return str(response)


#Odpowiedź z FastAPI: [{"type":"text","text":"Prezydentem Polski jest **Andrzej Duda**.","extras":{"signature":"EjQKMgEMOdbHPsO4j3synvW/fBl9jsvYVahWCk1Vw9y8FyOu9k5VYwixMTnhujLW2eZBV9dF"}}]
#nieaktualne ale on ma cutoff z stycznia 2025 i nie wie o Nawrockim.
