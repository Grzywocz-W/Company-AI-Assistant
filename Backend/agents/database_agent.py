#database_agent.py
import os
import sys
import re
import pickle
import torch
import numpy as np
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
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from models import modelsList
from modelSelector import createLLM
from configLoader import loadConfig
from agents.prompts.prompts import DATABASE_PROMPT
from neural_network.guardrail_network_model import GuardrailNN
try:
    from neural_network.guardrail_checker import GuardrailChecker
    _guardrail = GuardrailChecker()
    _guardrailAvailable = _guardrail._is_loaded
    if _guardrailAvailable:
        print("[DatabaseAgent] Model Guardrail został załadowany pomyślnie.")
    else:
        print("[DatabaseAgent] Model Guardrail niedostępny")
except Exception as e:
    print(f"[DatabaseAgent] Wystąpił nieoczekiwany błąd podczas odczytu modelu Guardrail: {e}")
    _guardrail = None
    _guardrailAvailable = False

api_key = os.getenv("Gemini_API_Key")
backendConfig = loadConfig('.env')


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


    def _checkGuardrail(self, id_klienta: int) -> tuple:
        if not _guardrailAvailable or _guardrail is None:
            return False, "Model Guardrail jest niedostępny - operacja nie dozwolona."

        try:
            is_allowed, probability, msg = _guardrail.sprawdz(id_klienta)

            print(f"[Guardrail] id={id_klienta} | prob={probability:.4f} | "
                  f"{'ZEZWOLONO' if is_allowed else 'ZABLOKOWANO'}")
            return is_allowed, msg

        except Exception as e:
            print(f"[DatabaseAgent] Błąd guardrail dla klienta {id_klienta}: {e}")
            #fail-safe
            return False, f"Błąd guardrail: {e}"


    def askDatabase(self, sql_query: str):
    #oczyszczenie z markdown, inaczej sql wywali error
        sql_query = sql_query.replace("```sql", "").replace("```", "").strip()

        prohibitedActions = ["DELETE", "UPDATE", "INSERT", "DROP", "ALTER"]
        hasProhibitedInQuery = False
        for action in prohibitedActions:
            if action in sql_query.upper():
                hasProhibitedInQuery = True
                break

        #Część odpowiedzialna za zabezpieczenia
        if hasProhibitedInQuery:
            match = re.search(r'id_klienta\s*=\s*(\d+)', sql_query, re.IGNORECASE)
            if match:
                id_klienta = int(match.group(1))
                is_allowed, guardrail_msg = self._checkGuardrail(id_klienta)
                if not is_allowed:
                    return (f"Operacja została zablokowana przez sieć neuronową do oceny ryzyka (Guardrail AI). "
                            f"Szczegóły: {guardrail_msg}")
        
        try:
            if not self.isAdmin:
                if hasProhibitedInQuery:
                    return "Odmowa dostępu. Niedozwolone polecenie dla zwykłego użytkownika."
                loginHost=backendConfig.get("DB_HOST_CUSTOMER")
                loginUser=backendConfig.get("DB_USER_CUSTOMER")
                loginPassword=backendConfig.get("DB_PASSWORD_CUSTOMER")
                loginDatabase=backendConfig.get("DB_NAME")
            else:
                loginHost=backendConfig.get("DB_HOST_ADMIN")
                loginUser=backendConfig.get("DB_USER_ADMIN")
                loginPassword=backendConfig.get("DB_PASSWORD_ADMIN")
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
                conn.commit()
                editedRows = cursor.rowcount
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

        except Exception as e:
            print(f"[AgentBazyDanych] Błąd agenta bazy danych: {e}")
            return f"Błąd systemu: Błąd agenta bazy danych {e}"

    


#Odpowiedź z FastAPI: [{"type":"text","text":"Prezydentem Polski jest **Andrzej Duda**.","extras":{"signature":"EjQKMgEMOdbHPsO4j3synvW/fBl9jsvYVahWCk1Vw9y8FyOu9k5VYwixMTnhujLW2eZBV9dF"}}]
#nieaktualne ale on ma cutoff z stycznia 2025 i nie wie o Nawrockim.
