import instructor
import litellm

_instructor_client = None

def get_litellm_instructor_client():
    global _instructor_client
    if _instructor_client is None:
        _instructor_client = instructor.from_litellm(litellm.acompletion)
    return _instructor_client
