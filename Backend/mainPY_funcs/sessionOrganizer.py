import time
import asyncio
from configLoader import loadConfig


backendConfig = loadConfig('config.txt')
sessionLifespan = int(backendConfig.get("SESSION_LIFESPAN_LIMIT", 1800))#1800s

#jeden użytkwonik = jedna sesja
sessionsDict= {}#'Michal', <obiekt>

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
