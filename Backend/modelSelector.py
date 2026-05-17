#modelSelector.py
import os
from models import modelsList

from langchain_google_genai import ChatGoogleGenerativeAI
#from langchain_openai import ChatOpenAI
from langchain_community.chat_models import ChatOllama

from configLoader import loadConfig

backendConfig = loadConfig('config.txt')
def createLLM(model_enum: modelsList,temperature = 0.0):
    fullModeName = model_enum.value
    aiCompany, modelName = fullModeName.split("/")

    if aiCompany == "google":
        googleLLM = ChatGoogleGenerativeAI(
            model=modelName,
            google_api_key=os.getenv("Gemini_API_Key"),
            temperature=temperature
            )
        return googleLLM  
##    elif aiCompany == "openai":Potem dodać OpenAI
##        openAiLLM = ChatOpenAI(
##            model=modelName,
##            api_key=os.getenv("OPENAI_API_KEY"),
##            temperature=temperature
##            )
##        return openAiLLM
    elif aiCompany == "ollama":
        OlamaLLM = ChatOllama(
            model=modelName,
            base_url=backendConfig.get("OLLAMA_URL"),
            temperature=temperature,
            )
        return OlamaLLM
    else:
        raise ValueError(f"Brak takiego modelu")
