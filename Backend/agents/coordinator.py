#coordinator.py
import os
###AI
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
####
from models import modelsList

api_key = os.getenv("Gemini_API_Key")


class CoordinatorAgent:
    def __init__(self, model: modelsList):
        
        self.agent = ChatGoogleGenerativeAI(
            model=model.value,#jest to enum, a nie tablica
            google_api_key=api_key
        )

        self.chatHistory = []


    def coordinatorResponse(self, inputText: str):
        inputMessage = HumanMessage(content=inputText)
        self.chatHistory.append(inputMessage)
        response = self.agent.invoke(self.chatHistory)
        self.chatHistory.append(response)###trzeba dodać!!!!

        ###odpowiedź zawiera też podpis(signature)
        response = response.content#wydobywamy tylko zawartość
        try:
            return response[0]["text"]#wydobywany pole text(niżej)
        except (IndexError, KeyError, TypeError):
            return str(response)

        return str(response)


#Odpowiedź z FastAPI: [{"type":"text","text":"Prezydentem Polski jest **Andrzej Duda**.","extras":{"signature":"EjQKMgEMOdbHPsO4j3synvW/fBl9jsvYVahWCk1Vw9y8FyOu9k5VYwixMTnhujLW2eZBV9dF"}}]
#nieaktualne ale on ma cutoff z stycznia 2025 i nie wie o Nawrockim.
