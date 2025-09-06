import os
import instructor
from openai import OpenAI
from litellm import completion

openai_client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'), timeout=3600)
litellm_client = instructor.from_litellm(completion)
