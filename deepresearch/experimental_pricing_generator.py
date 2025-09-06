import openai
import os
from typing import List
from datastore.types import PricingExperimentPydantic


def invoke_agent():
    client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": "Your input prompt here"}]
    )
    return response.choices[0].message.content


def invoke_orchestrator(experiments: List[PricingExperimentPydantic]) -> List[PricingExperimentPydantic]:
    return experiments
