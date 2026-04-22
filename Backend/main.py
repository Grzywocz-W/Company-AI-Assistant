import os
####API
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
###AI
from agents.coordinator import CoordinatorAgent
from models import modelsList



react = FastAPI()

origins =[
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    ########################
    "http://localhost:54557",
    "http://127.0.0.1:54557",
]

react.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],  
    allow_headers=["*"],  
)
model = modelsList.gemi3_1_fl
#coordAgent = CoordinatorAgent(model=model)

#jeden użytkwonik = jedna sesja
sessionsDict= {}#'Michal', <obiekt>

class messageRequest(BaseModel):
    sessionID: str#liczba dla klientów, tekst dla admina itp.
    text: str

@react.post("/chat")
def feedback(request: messageRequest):
    try:
        currentSession = request.sessionID
        if currentSession not in sessionsDict:
            sessionsDict[currentSession] = CoordinatorAgent(model=model)
            
        response = sessionsDict[currentSession].coordinatorResponse(request.text)
        
        #return {'result': response.content}
        return {'result': response}
    except Exception as e:
        return {'result': f'Error {str(e)}'}


