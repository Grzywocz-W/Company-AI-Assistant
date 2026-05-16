#databaseagent.py
import os
import mysql.connector
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

api_key = os.getenv("Gemini_API_Key")

# Na górze pliku database_agent.py
DB_HOST = "localhost"
DB_USER = "root"
DB_PASSWORD = ""
DB_NAME = "sklep"


class DataBaseAgent:
    def __init__(self, model: modelsList):
        self.agent = createLLM(model, temperature=0.1)
##        self.agent = ChatGoogleGenerativeAI(
##            model=model.value,#jest to enum, a nie tablica
##            google_api_key=api_key,
##            temperature=0.1#małą kreatywność
##            )
        self.isAdmin = False

        #self.chatHistory = []

        self.tools =[
            Tool(name = "dataBaseQuerryTOOL",
                 func= self.askDataBase,
                 description = "Używaj by zadać pytanie do bazy danych"
                 ),
            ]
        
        #dodać zabezpieczenia aby nie zwrócił klientowi zapytania
        SCHEMA_INFO = """
        Tabele i kolumny w bazie 'sklep':
        - produkty (id, nazwa, cena, opis)
        - pracownicy (id, imie, nazwisko, stanowisko)
        """

        systemPrompt = """
        Jesteś agentem od zapytań SQL ds. Bazy Danych 'sklep'. 
        Otrzymujesz polecenie od Koordynatora. Masz za zadanie przetłumaczenie ich na SQL i wykonanie tylko tego zapytania.
        
        Struktura bazych danych:
        - produkty (id, nazwa, cena, opis)
        - pracownicy (id, imie, nazwisko, stanowisko)

        ZASADY:
        1. ZAWSZE używaj narzędzia dataBaseQuerryTOOL.
        2. Do zapytania podawaj tylko treść w języku SQL (zaczynającą się od SELECT).
        3. ZAKAZ używania poleceń: DELETE, DROP, UPDATE, INSERT chyba, że dostaniesz info, iż zalogował się admin.
        4. Jeśli zapytanie dotyczy tekstu, korzystaj z konstrukcji: LIKE '%fraza%'.
        
        Narzędzia: {tools}
        
        Format:
        Question: Rozkaz od Koordynatora
        Thought: Musisz napisać zapytanie SQL.
        Action: {tool_names}
        Action Input: SELECT FROM
        Observation: Wynik z bazy danych
        Thought: Masz dane. Sformułuj raport.
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

    def askDataBase(self, sql_query: str):
    #oczyszczenie z markdown, inaczej sql wywali error
        sql_query = sql_query.replace("```sql", "").replace("```", "").strip()

        prohibitedActions = ["DELETE", "UPDATE", "INSERT", "DROP", "ALTER"]
        hasProhibitedInQuery = False
        for action in prohibitedActions:
            if action in sql_query.upper():
                hasProhibitedInQuery = True
                break
        
        try:
            if not self.isAdmin:#zazwyczaj nie będzie adminem a więc not False = True
                if hasProhibitedInQuery:
                    return "Odmowa dostępu. Niedozwolone polecenie"
                loginHost=DB_HOST
                loginUser=DB_USER
                loginPassword=DB_PASSWORD
                loginDatabase=DB_NAME
            else:# dostęp admina. Potem się zmieni hasło
                loginHost=DB_HOST
                loginUser=DB_USER
                loginPassword=DB_PASSWORD
                loginDatabase=DB_NAME
                
            conn = mysql.connector.connect(
                host=loginHost,
                user=loginUser,
                password=loginPassword,
                database=loginDatabase
            )
            
            cursor = conn.cursor(dictionary=True)
            cursor.execute(sql_query)

            if hasProhibitedInQuery:
                conn.commit() # pozwala na zmainy do bazy
                editedRows = cursor.rowcount #ile usuniętych rekordów
                cursor.close()
                conn.close()
                return f"Dokonano modyfikacji {editedRows} wierszy"
            
            wyniki = cursor.fetchall()
            
            cursor.close()
            conn.close()
            if not wyniki:
                return f"Wykonano zapytanie: {sql_query}, ale baza jest pusta lub nic nie pasuje."
                
            return f"Dane z bazy: {str(wyniki)}"

        except mysql.connector.Error as err:
            return f"BŁĄD MySQL: {err} | Próbowano wykonać: {sql_query}"


    def dataBaseAgentResponse(self, inputText: str):

        if self.isAdmin:
            additionalInfo =" [SYSTEM OVERRIDE]: Użytkownik zalogował się jako admin. Masz teraz dostęp do INSERT, UPDATE oraz DELETE TYM ZAPYTANIU I TYLKO W TYM."
        else:
            additionalInfo= "[SYSTEM INFO]: Użytkownik to ZWYKŁY GOŚĆ."
            
        response = self.agentExecutor.invoke(
            {"input": additionalInfo + inputText}
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
