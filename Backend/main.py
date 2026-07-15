#!pip install python-multipart
#!pip install bcrypt
import os
import traceback
### zwalnanie pamięci
import time
import asyncio
from contextlib import asynccontextmanager
#obsługa PDF'a
#import io 
#import pypdf
####API
import bcrypt
import uvicorn
from fastapi import FastAPI, File, UploadFile, Form,Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from fastapi.responses import StreamingResponse
import json
###AI
#from agents.coordinator import CoordinatorAgent
from models import modelsList
from helpers import extractFromPDF
from configLoader import loadConfig
from mainPY_funcs.sessionOrganizer import sessionsDict, checkSessionLifespan


backendConfig = loadConfig('config.txt')


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
    "http://192.168.1.15:54557",
]

react.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],  
    allow_headers=["*"],  
)


defaultModel ="gemi3_1_fl"

#backendConfig = loadConfig('config.txt')
modelName = backendConfig.get("MAIN_MODEL", defaultModel)

try:
    model = modelsList[modelName]
except Exception as e:
    print("Nie ma takiego modelu")
    model = modelsList[defaultModel]

#model = modelsList.gemi3_1_fl
#coordAgent = CoordinatorAgent(model=model)


#!!!!!DODAĆ ZWALNANIE PAMIĘCI!!!!!!!


#przez dodanie załącznika pdf nie wysyłamy już Message requesta
#class messageRequest(BaseModel):
#    sessionID: str#liczba dla klientów, tekst dla admina itp.
#    text: str


acceptedFilesFormat = ['PDF']#na przyszłość do rozbudowy


@react.post("/chat")
async def feedback(
    sessionID: str = Form(...),
    request: str = Form(...),#ID i prompt są teraz jak formularz
    #isAdmin:bool = Form(False),
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
                'isAdmin': False
            }
        else:
            sessionsDict[currentSession]['born'] = now

        adminPrivileges = sessionsDict[currentSession].get('isAdmin', False)#domyślnie fałsz

        if attachedFile and attachedFile.filename.endswith('.pdf'):
            pdfContent = await attachedFile.read()#jest to funkcja asynchroniczna
            textFromPdf = extractFromPDF(pdfContent)
            
            request = f"Zawartość pliku PDF załączona przez użytkownika: \n {textFromPdf}  \n Pytanie użytkownika: \n" + request

        if adminPrivileges:
            request = "[SYSTEM OVERRIDE]: Użytkownik zalogował się jako admin. Może edytować bazę danych.\n" + request
            
        queue = asyncio.Queue()

        async def executeAgent():
            try:
                agent = sessionsDict[currentSession]['agent']
                response =await agent.coordinatorResponse(request, queue, adminPrivileges)
                await queue.put(json.dumps(
                    {"type": "final", "data": response}
                    ))

            except Exception as e:
                await queue.put(json.dumps({"type": "error", "data": str(e)}))
            finally:
                await queue.put(None)
                
        async def responseStream():
            receiver =asyncio.create_task(executeAgent())
            try:
                while True:
                    messageTMP = await queue.get()
                    if messageTMP is None:
                        break
                    
                    yield f"{messageTMP}\n"
            finally:
                await receiver
        return StreamingResponse(responseStream(), media_type="application/x-ndjson")
        #response = sessionsDict[currentSession]['agent'].coordinatorResponse(request.text)
        #response = sessionsDict[currentSession]['agent'].coordinatorResponse(request)
        
        #return {'result': response.content}
        #return {'result': response}
    except Exception as e:
        print(f"\n[!!!] KRYTYCZNY BŁĄD W MAIN.PY: {str(e)}\n")
        
        traceback.print_exc()
        
        return {'result': f'Error {str(e)}'}




@react.get("/check-ip")
async def checkUserIp(request: Request):
    userIp = request.headers.get("X-Forwarded-For", request.client.host).split(",")[0].strip()
    
    configAdminIps = backendConfig.get("ALLOWED_ADMIN_IP")
    adminIps = configAdminIps.split(",")
    
    adminIpList = []
    for ip in adminIps:
        adminIpList.append(ip.strip())
        
    adminControl = False
    if userIp in adminIpList:
        adminControl = True
    return {"is-admin-control-allowed": adminControl}


class AdminLoginRequest(BaseModel):
    password: str
    sessionID: str


@react.post("/admin-login")
async def checkAdminPassword(request: AdminLoginRequest):
    passwordHash = backendConfig.get("ADMIN_PASSWORD")
    if not passwordHash:
        return {"status": "error", "message": "Brak hasła"}


    try:
        isCorrect = bcrypt.checkpw(
            request.password.encode('utf-8'),
            passwordHash.encode('utf-8')
            )
        
        if isCorrect:
            now = time.time()
            if request.sessionID not in sessionsDict:
                sessionsDict[request.sessionID]={
                    'agent': CoordinatorAgent(model=model),
                    'born': now,
                    'isAdmin': True#dajemy admina
                    }
            else:
                sessionsDict[request.sessionID]['isAdmin'] = True
                sessionsDict[request.sessionID]['born'] = now
                
            feedback = {
                "status":"correct",
                "message": "Zalogowano na admina"
                }
            return feedback
        else:
            feedback = {
                "status":"error",
                "message": "loginErr4r"
                }
            return feedback
    except Exception as e:
        print(f"Błąd logowania: {e}")
        return {"status": "error", "message": "Błąd backendu"}



class AdminLogoutRequest(BaseModel):
    sessionID: str


@react.post("/admin-logout")
async def adminLogout(request: AdminLogoutRequest):
    try:
        if request.sessionID in sessionsDict:
            sessionsDict[request.sessionID]['isAdmin']=False
                
            feedback = {
                "status":"correct",
                "message": "Wylogowano admina"
                }
            return feedback
    except Exception as e:
        print(f"Błąd wylogowania: {e}")
        return {"status": "error", "message": "Błąd backendu-wylogowanie"}


if __name__ == "__main__":
    uvicorn.run("main:react", host="127.0.0.1", port=8000, reload=True)

