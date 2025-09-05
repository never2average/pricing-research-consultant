from datastore.models import Product
from utils.openai_client import openai_client
from .prompts import cashflow_analysis_prompt


def agent(product_id=None, pricing_research=None):
    """
    Cashflow Analyst Agent
    Analyzes financial impact and cashflow implications of pricing strategies
    """
    product = Product.objects.get(id=product_id)
    input_data = f"""
## Product
{product.name}

## Core Features
{product.features_description_summary}

## Ideal Customer Profile
{product.icp_description}

## Pricing Research Context
{pricing_research or "No pricing research provided"}
"""
    
    response = openai_client.responses.create(
        model="o3-deep-research",
        instructions=cashflow_analysis_prompt,
        input=input_data,
        tools=[
            {"type": "web_search_preview"},
            {
                "type": "file_search",
                "vector_store_ids": [
                    "vs_cxOy9F7MqC5LnBvAdrXGdxLw"
                ]
            }
        ]
    )
    
    return response.content[0].text


def refinement_agent(product_id=None, experimental_pricing_research=None, positioning_analysis=None, persona_simulation=None):
    """
    Cashflow Analyst Refinement Agent
    Refines cashflow analysis based on positioning and persona simulation feedback
    """
    product = Product.objects.get(id=product_id)
    input_data = f"""
## Product
{product.name}

## Experimental Pricing Research
{experimental_pricing_research or "No experimental pricing provided"}

## Positioning Analysis Feedback
{positioning_analysis or "No positioning analysis provided"}

## Persona Simulation Feedback
{persona_simulation or "No persona simulation provided"}
"""
    
    response = openai_client.responses.create(
        model="o3-deep-research",
        instructions="Refine cashflow analysis based on positioning and persona feedback. Focus on financial viability, revenue projections, and risk assessment of the proposed pricing model.",
        input=input_data,
        tools=[
            {"type": "web_search_preview"},
            {
                "type": "file_search",
                "vector_store_ids": [
                    "vs_cxOy9F7MqC5LnBvAdrXGdxLw"
                ]
            }
        ]
    )
    
    return response.content[0].text
