from openai import AsyncOpenAI
import os

_client = None

def get_openai_client():
    global _client
    if _client is None:
        _client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    return _client
