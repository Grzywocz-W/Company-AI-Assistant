#!pip install python-multipart
import os
### zwalnanie pamięci
import time
import asyncio
from contextlib import asynccontextmanager
#obsługa PDF'a
#import io 
#import pypdf
####API
import uvicorn
from fastapi import FastAPI, File, UploadFile, Form,Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from fastapi.responses import StreamingResponse
import json
###AI
from agents.coordinator import CoordinatorAgent
from models import modelsList
from helpers import extractFromPDF
from configLoader import loadConfig


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


defaultModel ="gemi3_1_fl"

backendConfig = loadConfig('config.txt')
modelName = backendConfig.get("MAIN_MODEL", defaultModel)

try:
    model = modelsList[modelName]
except Exception as e:
    print("Nie ma takiego modelu")
    model = modelsList[defaultModel]

#model = modelsList.gemi3_1_fl
#coordAgent = CoordinatorAgent(model=model)

#jeden użytkwonik = jedna sesja
sessionsDict= {}#'Michal', <obiekt>
#!!!!!DODAĆ ZWALNANIE PAMIĘCI!!!!!!!


#przez dodanie załącznika pdf nie wysyłamy już Message requesta
#class messageRequest(BaseModel):
#    sessionID: str#liczba dla klientów, tekst dla admina itp.
#    text: str


acceptedFilesFromat = ['PDF']#na przyszłość do rozbudowy


@react.post("/chat")
async def feedback(
    sessionID: str = Form(...),
    request: str = Form(...),#ID i prompt są teraz jak formularz
    attachedFile: UploadFile = File(None)# jako opcjonalny plik
    ):
#async def feedback(request: messageRequest):#asynchroniczna aby otrzymać pdf'a
    try:
        #currentSession = request.sessionID
        currentSession = sessionID
        
        now = time.time()
        if currentSession not in sessionsDict:
            sessionsDict[currentSession] ={#nie można dać do następnej linijki
                'agent':CoordinatorAgent(model=model),
                'born': now,#obecny czas
            }
        else:
            sessionsDict[currentSession]['born'] = now

        if attachedFile and attachedFile.filename.endswith('.pdf'):
            pdfContent = await attachedFile.read()#jest to funkcja asynchroniczna
            textFromPdf = extractFromPDF(pdfContent)
            
            request = f"Zawartość pliku PDF załączona przez użytkownika: \n {textFromPdf}  \n Pytanie użytkownika: \n" + request
            
        queue = asyncio.Queue()

        async def executeAgent():
            try:
                agent = sessionsDict[currentSession]['agent']
                response =await agent.coordinatorResponse(request, queue)
                await queue.put(json.dumps(
                    {"type": "final", "data": response}
                    ))

            except Exception as e:
                await queue.put(json.dumps({"type": "error", "data": str(e)}))
            finally:
                await queue.put(None)
                
        async def responseStream():
            reciver =asyncio.create_task(executeAgent())
            
            while True:
                messageTMP = await queue.get()
                if messageTMP is None:
                    break
                
                yield f"{messageTMP}\n"

        return StreamingResponse(responseStream(), media_type="application/x-ndjson")
        #response = sessionsDict[currentSession]['agent'].coordinatorResponse(request.text)
        #response = sessionsDict[currentSession]['agent'].coordinatorResponse(request)
        
        #return {'result': response.content}
        #return {'result': response}
    except Exception as e:
        return {'result': f'Error {str(e)}'}




@react.get("/check-ip")
async def checkUserIp(request: Request):
    userIp = request.headers.get("X-Forwarded-For", request.client.host).split(",")[0].strip()
    
    configAdminIps = backendConfig.get("ALLOWED_ADMIN_IP", "127.0.0.1")
    adminIps = configAdminIps.split(",")
    
    adminIpList = []
    for ip in adminIps:
        adminIpList.append(ip.strip())
        
    adminControl = False
    if userIp in adminIpList:
        adminControl = True
    return {"is-admin-control-allowed": adminControl}
    

