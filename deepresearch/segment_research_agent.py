from typing import List
from datastore.types import PricingExperimentPydantic
from utils.openai_client import get_openai_client


def invoke_agent(pricing_experiment: PricingExperimentPydantic):
    client = get_openai_client()
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": "Your input prompt here"}]
    )
    return response.choices[0].message.content


def invoke_orchestrator(experiments: List[PricingExperimentPydantic]) -> List[PricingExperimentPydantic]:
    return experiments
