#models
from enum import Enum

class modelsList(Enum):
    gemma4_31b = "google/gemma-4-31b-it"
    gemi3_5_fl = "google/gemini-3.5-flash-lite"
    gemi3_1_fl = "google/gemini-3.1-flash-lite"

    gpt4o_mini = "openai/gpt-4o-mini"

    ollama_llama3 = "ollama/llama3"

    ollama_qwen25 = "ollama/qwen2.5:7b"

    #ollama_deepseek_r1 = "ollama/deepseek-r1:8b"
