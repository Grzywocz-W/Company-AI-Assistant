#RAG_agent.py
import os
###AI
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_classic.agents import create_react_agent, AgentExecutor
from langchain_core.prompts import PromptTemplate
from langchain_core.chat_history import InMemoryChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.tools import Tool
####RAG
from langchain_community.vectorstores import FAISS
###
from models import modelsList
from modelSelector import createLLM
from agents.prompts.prompts import RAG_PROMPT
#
api_key = os.getenv("Gemini_API_Key")



class RagAgent:
    def __init__(self, model: modelsList,db_path: str = "vectorDB"):
        self.model = createLLM(model, temperature=0.0)
##        self.agent = ChatGoogleGenerativeAI(
##            model=model.value,#jest to enum, a nie tablica
##            google_api_key=api_key,
##            temperature=0.1#małą kreatywność
##            )

        
        embeddingModel = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001", google_api_key=api_key)

        try:
            self.vectorDataBase = FAISS.load_local(
                folder_path=db_path, 
                embeddings=embeddingModel, 
                allow_dangerous_deserialization=True
                )
        except Exception as e:
            print(f"[RAG_agent] nie da się załadować bazy wektorowej: {e}")
            self.vectorDataBase = None

        def searchVectorDataBase(sentence: str):# dodano str, bo był błąd podczas pytania o liczby
            if self.vectorDataBase == None:
                return "Błąd backendu. Baza wektorowa niezdefiniowana"
            try:
                mostAccurateDocuments = self.vectorDataBase.similarity_search(sentence,k=3)#potestować dla różnego k
                result = ""
                for doc in mostAccurateDocuments:
                    result += doc.page_content
                    result += "\n\n...\n\n"
                return result
            except Exception as e:
                print(f"Błąd przeszukiwania dokumentów: {e}")
                return(f"Błąd przeszukiwania dokumentów: {e}")



        
        
        self.tools =[
            Tool(name = "searchDocuments",
                 func= searchVectorDataBase,
                 description = "Używaj do przeszukiwania dokumentów"
                 ),
            ]
        

        
        

        prompt = PromptTemplate.from_template(RAG_PROMPT)
        reactAgent = create_react_agent(self.model, self.tools, prompt)

        self.agentExecutor = AgentExecutor(
            agent = reactAgent,
            tools = self.tools,
            verbose=True,#wypisuje w konsoli jak myśli
            handle_parsing_errors=True,
            )


    def ragAgentResponse(self, inputText: str):
        try:
            response = self.agentExecutor.invoke(
                {"input": inputText}
                )
        
            if isinstance(response, dict):#czasem zwracany jest słownik, a czasem nie
                return response.get("output", str(response))#trzba sparsować na str
            else:
                return str(response)
        
        except Exception as e:
            print(f"[RAG_agent] Błąd wywołania agenta: {e}")
            return f"Błąd komunikacji z agentem RAG: {e}"


