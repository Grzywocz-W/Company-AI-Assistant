#models
from enum import Enum

class modelsList(Enum):
    gema3_27b = "google/gemma-3-27b-it"
    gemi3_5_fl = "google/gemini-3.5-flash-lite"

    gpt4o_mini = "openai/gpt-4o-mini"

    ollama_llama3 = "ollama/llama3"

    ollama_qwen25 = "ollama/qwen2.5"
