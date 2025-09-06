import os
from typing import Any
import instructor
from openai import OpenAI
from litellm import completion

openai_client: OpenAI = OpenAI(api_key=os.getenv('OPENAI_API_KEY'), timeout=3600)
litellm_client: Any = instructor.from_litellm(completion)
