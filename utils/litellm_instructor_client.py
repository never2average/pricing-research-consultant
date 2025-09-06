import instructor
import litellm
import os

_instructor_client = None

def get_litellm_instructor_client():
    global _instructor_client
    if _instructor_client is None:
        litellm.api_key = os.getenv("OPENAI_API_KEY")
        _instructor_client = instructor.patch(litellm.completion)
    return _instructor_client
