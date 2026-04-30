import os
### zwalnanie pamięci
import time
import asyncio
from contextlib import asynccontextmanager
####API
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
###AI
from agents.coordinator import CoordinatorAgent
from models import modelsList

sessionLifespan = 1800#sekund 30 min.

async def checkSessionLifespan():
    while True:
        await asyncio.sleep(300)#co 5 minut
        now = time.time()#obecny czas

        sessionsToDelete = []
        for sesID, data in sessionsDict.items():
            if now - data['born'] > sessionLifespan:
                sessionsToDelete.append(sesID)

        for sesID in sessionsToDelete:
            sessionsDict.pop(sesID)

@asynccontextmanager #bez tego nie działa
async def sessionGarbageCollector(app: FastAPI):
    garbageCollector = asyncio.create_task(checkSessionLifespan())
    yield
    garbageCollector.cancel()#wyłączyć po zatrzymaniu

react = FastAPI(lifespan = sessionGarbageCollector )

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
#!!!!!DODAĆ ZWALNANIE PAMIĘCI!!!!!!!
class messageRequest(BaseModel):
    sessionID: str#liczba dla klientów, tekst dla admina itp.
    text: str

@react.post("/chat")
def feedback(request: messageRequest):
    try:
        currentSession = request.sessionID

        now = time.time()
        if currentSession not in sessionsDict:
            sessionsDict[currentSession] ={#nie można dać do następnej linijki
                'agent':CoordinatorAgent(model=model),
                'born': now,#obecny czas
            }
        else:
            sessionsDict[currentSession]['born'] = now
            
        response = sessionsDict[currentSession]['agent'].coordinatorResponse(request.text)
        
        #return {'result': response.content}
        return {'result': response}
    except Exception as e:
        return {'result': f'Error {str(e)}'}


