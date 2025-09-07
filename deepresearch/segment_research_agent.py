import copy
from typing import List
from pydantic import BaseModel, Field
from datastore.models import CustomerSegment
from utils.openai_client import get_openai_client
from datastore.types import PricingExperimentPydantic, ExperimentGenStage
from utils.litellm_instructor_client import get_litellm_instructor_client


class SegmentSelectionResult(BaseModel):
    selected_segments: List[str] = Field(description="The list of segment names that were recommended in the analysis.")
    reasoning: str = Field(description="The reasoning for the segment selection.")


async def invoke_agent(pricing_experiment: PricingExperimentPydantic):
    client = get_openai_client()
    instructor_client = get_litellm_instructor_client()
    

    all_segments = CustomerSegment.objects.only("segment_name", "segment_description", "segment_usage_summary").all()
    segments_text = "\n\n".join([
        f"- {segment.segment_name}: {segment.segment_description}\n\n{segment.segment_usage_summary}" for segment in all_segments
    ])
    
    system_prompt = """
You are a senior B2B pricing strategist. Your task is to evaluate which customer segments are the best fit for a pricing experiment and explain why.

RULES
- Use only the customer segments provided in "Available Customer Segments". Do not invent new segments.
- When naming segments, use the exact names as provided.
- If no segments are provided, explain what information is missing and do not fabricate results.
- Prefer clear, concise, decision-oriented writing. Avoid generic fluff.
- Think step-by-step: make your criteria explicit, then evaluate each segment against those criteria, then decide.

OUTPUT FORMAT (use these exact section headers)
1) Context
2) Evaluation Framework
3) Segment Assessments
4) Recommendations
5) Deprioritized Segments
6) Risks and Mitigations
7) Final Decision

FINAL DECISION FORMAT
- Provide a single line that starts with: Selected Segments: <comma-separated exact segment names>
- Keep the list to the most relevant segments only.
"""

    deep_research_prompt = f"""
You are a pricing strategy expert conducting deep research on customer segments for a pricing experiment.

CONTEXT
- Product: {pricing_experiment.product.product_name if pricing_experiment.product else 'Unknown'}
- Product Description: {pricing_experiment.product.product_description if pricing_experiment.product else 'Not provided'}
- Product Industry: {pricing_experiment.product.product_industry if pricing_experiment.product else 'Not specified'}
- Product ICP Summary: {pricing_experiment.product.product_icp_summary if pricing_experiment.product else 'Not provided'}
- Product Seed Context: {pricing_experiment.product_seed_context if pricing_experiment.product_seed_context else 'Not provided'}
- Experiment Objective: {pricing_experiment.objective}
- Use Case/Rationale: {pricing_experiment.usecase}

Available Customer Segments (use exact names, do not invent):
{segments_text}
"""
    
    deep_research_response = await client.responses.create(
        model="gpt-5",
        instructions=system_prompt,
        input=deep_research_prompt,
        reasoning={"effort": "high"},
        truncation="auto",
        max_output_tokens=8192
    )
  
    parsing_prompt = f"""
Selected Segments:
{deep_research_response.output_text}
"""
    system_prompt_structured_output = """
You are a pricing strategist extracting a clean, structured decision from an analysis.

TASK
- Read the analysis.
- Return the final list of selected segments using the exact names that appear in the input segment list.
- If the analysis includes a line starting with "Selected Segments:", use those names verbatim.
- If that line is missing, infer the top recommended segments from the "Recommendations" section.
- If no valid segments are present, return an empty list.

REASONING FIELD
- Provide a concise 2-4 sentence summary of why these segments were selected.
"""
    
    structured_result = await instructor_client(
        model="claude-sonnet-4-20250514",
        api_key="",
        response_model=SegmentSelectionResult,
        messages=[{"role": "system", "content": system_prompt_structured_output},{"role": "user", "content": parsing_prompt}],
        temperature=0.0
    )
    
    return structured_result


async def invoke_orchestrator(experiments: List[PricingExperimentPydantic]) -> List[PricingExperimentPydantic]:
    result_experiments = []
    
    for experiment in experiments:
        selection_result = await invoke_agent(experiment)
        selected_segment_names = selection_result.selected_segments
        selected_segments = CustomerSegment.objects(segment_name__in=selected_segment_names)
        
        for segment in selected_segments:
            new_experiment = copy.deepcopy(experiment)
            new_experiment.relevant_segment = segment.segment_usage_summary
            new_experiment.experiment_gen_stage = ExperimentGenStage.SEGMENTS_LOADED
            result_experiments.append(new_experiment)
        
    return result_experiments
