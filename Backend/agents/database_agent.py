#database_agent.py
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
from configLoader import loadConfig
from agents.prompts.prompts import DATABASE_PROMPT

api_key = os.getenv("Gemini_API_Key")

backendConfig = loadConfig('config.txt')
# Na górze pliku database_agent.py


class DatabaseAgent:
    def __init__(self, model: modelsList):
        self.model = createLLM(model, temperature=0.1)
##        self.agent = ChatGoogleGenerativeAI(
##            model=model.value,#jest to enum, a nie tablica
##            google_api_key=api_key,
##            temperature=0.1#małą kreatywność
##            )
        self.isAdmin = False

        #self.chatHistory = []

        self.tools =[
            Tool(name = "databaseQueryTool",
                 func= self.askDatabase,
                 description = "Używaj by zadać pytanie do bazy danych"
                 ),
            ]

        

        prompt = PromptTemplate.from_template(DATABASE_PROMPT)
        reactAgent = create_react_agent(self.model, self.tools, prompt)

        self.agentExecutor = AgentExecutor(
            agent = reactAgent,
            tools = self.tools,
            verbose=True,#wypisuje w konsoli jak myśli
            handle_parsing_errors=True,
            )

    def askDatabase(self, sql_query: str):
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
                loginHost=backendConfig.get("DB_HOST_CUSTOMER")
                loginUser=backendConfig.get("DB_USER_CUSTOMER")
                loginPassword=backendConfig.get("DB_PASSWORD_CUSTOMER")
                loginDatabase=backendConfig.get("DB_NAME")
            else:# dostęp admina. Potem się zmieni hasło
                loginHost=backendConfig.get("DB_HOST_ROOT")
                loginUser=backendConfig.get("DB_USER_ROOT")
                loginPassword=backendConfig.get("DB_PASSWORD_ROOT")
                loginDatabase=backendConfig.get("DB_NAME")
                
            conn = mysql.connector.connect(
                host=loginHost,
                user=loginUser,
                password=loginPassword,
                database=loginDatabase
            )
            
            cursor = conn.cursor(dictionary=True)
            cursor.execute(sql_query)

            if hasProhibitedInQuery:
                conn.commit() # pozwala na zmiany do bazy
                editedRows = cursor.rowcount #ile usuniętych rekordów
                cursor.close()
                conn.close()
                return f"Dokonano modyfikacji {editedRows} wierszy"
            
            results = cursor.fetchall()
            
            cursor.close()
            conn.close()
            if not results:
                return f"Wykonano zapytanie: {sql_query}, ale baza jest pusta lub nic nie pasuje."
                
            return f"Dane z bazy: {str(results)}"

        except mysql.connector.Error as err:
            return f"BŁĄD MySQL: {err} | Próbowano wykonać: {sql_query}"


    def databaseAgentResponse(self, inputText: str):

        if self.isAdmin:
            additionalInfo =" [SYSTEM OVERRIDE]: Użytkownik zalogował się jako admin. Masz teraz dostęp do INSERT, UPDATE oraz DELETE w TYM ZAPYTANIU I TYLKO W TYM."
        else:
            additionalInfo= "[SYSTEM INFO]: Użytkownik to ZWYKŁY GOŚĆ."
        try:    
            response = self.agentExecutor.invoke(
                {"input": additionalInfo + inputText}
                )
            
            if isinstance(response, dict):
                return response.get("output", str(response))
            else:
                return str(response)

        ###odpowiedź zawiera też podpis(signature)
        #response = response.content#wydobywamy tylko zawartość
        except Exception as e:
            print(f"[AgentBazyDanych] Błąd agenta bazy danych: {e}")
            return f"Błąd systemu: Błąd agenta bazy danych {e}"

    


#Odpowiedź z FastAPI: [{"type":"text","text":"Prezydentem Polski jest **Andrzej Duda**.","extras":{"signature":"EjQKMgEMOdbHPsO4j3synvW/fBl9jsvYVahWCk1Vw9y8FyOu9k5VYwixMTnhujLW2eZBV9dF"}}]
#nieaktualne ale on ma cutoff z stycznia 2025 i nie wie o Nawrockim.
