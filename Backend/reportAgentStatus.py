#reportAgentStatus.py
import json
import asyncio
from enum import Enum
#from langchain.callbacks.base import AsyncCallbackHandler
from langchain_core.callbacks import AsyncCallbackHandler


class AgentCallingStatus(str, Enum):
    DATABASE = "DATABASE"
    RAG = "RAG"
    INTERNET = "INTERNET"
    THINKING = "THINKING"

class AgentStatusAsyncCallbackHandler(AsyncCallbackHandler):
    
    def __init__(self, queue: asyncio.Queue):
        self.queue = queue
    #===========WYCISZENIE on changed LangChaina ===========#
    async def on_chat_model_start(self, *args, **kwargs):
        pass

    async def on_llm_start(self, *args, **kwargs):
        pass

    async def on_chain_start(self, *args, **kwargs):
        pass
        
    async def on_tool_end(self, *args, **kwargs):#powrtó do myslenia
        await self.queue.put(
                json.dumps(
                    {
                        "type": "status",
                        "data": AgentCallingStatus.THINKING.value
                        })
                )
        
    async def on_chain_end(self, *args, **kwargs):
        pass
            #nazwa to wymóg langChaina
    async def on_tool_start(self, serialized, input_str, **kwargs):
        agentName = serialized.get("name")
        status = None

        if agentName == "AgentBazyDanych":
            status = AgentCallingStatus.DATABASE
        elif agentName == "AgentPrzeszukaniaDokumentów":
            status = AgentCallingStatus.RAG
        elif agentName == "AgentPrzeszukaniaInternetu":
            status = AgentCallingStatus.INTERNET
            
        if status:
            await self.queue.put(
                json.dumps(
                    {
                        "type": "status",
                        "data": status.value,
                        })
                )

