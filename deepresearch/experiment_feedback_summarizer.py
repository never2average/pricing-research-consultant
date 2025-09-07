import asyncio
import json
from typing import List
from datastore.types import PricingExperimentPydantic, ExperimentGenStage
from utils.openai_client import get_openai_client


async def invoke_agent(pricing_experiment: PricingExperimentPydantic):
    client = get_openai_client()
    
    system_prompt = """
You are an experiment analysis expert specializing in pricing strategy evaluation. Analyze experiment results and provide actionable insights for decision-making.

FEEDBACK ANALYSIS FRAMEWORK:
1. Results Summary - Key outcomes vs original hypotheses and expectations
2. Success Metrics Analysis - Performance against defined KPIs and benchmarks
3. Customer Behavior Insights - How customers responded to pricing changes
4. Financial Impact Assessment - Actual vs projected financial outcomes  
5. Learnings and Insights - What worked, what didn't, and why
6. Strategic Implications - Impact on broader pricing strategy and positioning
7. Next Steps Recommendations - Concrete actions based on results

ANALYSIS DIMENSIONS:
- Quantitative performance (revenue, usage, conversion rates, churn)
- Qualitative feedback (customer satisfaction, sales team input, support tickets)
- Competitive responses and market reactions
- Operational impacts and execution challenges  
- Statistical significance and confidence in results
- Unexpected outcomes and their root causes

OUTPUT FORMAT:
Provide structured JSON with these exact keys:
- experiment_summary: High-level overview of what was tested and outcomes
- hypothesis_validation: Whether original hypotheses were confirmed or rejected
- key_metrics_performance: Actual vs target performance on key metrics
- customer_behavior_insights: How customers responded to changes
- financial_impact_actual: Real financial outcomes vs projections
- lessons_learned: Key insights and learnings from the experiment
- strategic_implications: What this means for broader pricing strategy
- recommendations: Specific next steps and follow-up actions
- confidence_level: How confident we are in the results and conclusions

REQUIREMENTS:
- Be objective and data-driven in analysis
- Highlight both positive and negative outcomes
- Provide specific recommendations with clear rationale
- Include confidence levels and statistical significance where applicable
- Connect learnings to broader strategic implications
"""

    product_name = pricing_experiment.product.product_name if pricing_experiment.product else "Unknown Product"
    experimental_plan = pricing_experiment.experimental_pricing_plan or "No pricing plan available"
    simulation_result = pricing_experiment.simulation_result or "No simulation data available"
    cashflow_analysis = pricing_experiment.cashflow_feasibility_comments or "No cash flow analysis available"
    objective = pricing_experiment.objective or "Not specified"
    usecase = pricing_experiment.usecase or "Not specified"
    
    deployment_status = "Deployed" if pricing_experiment.experiment_is_deployed else "Not deployed"
    deployed_date = pricing_experiment.experiment_deployed_on.isoformat() if pricing_experiment.experiment_deployed_on else "Not deployed"

    user_prompt = f"""
EXPERIMENT CONTEXT:
Product: {product_name}
Experiment Objective: {objective}
Use Case: {usecase}
Deployment Status: {deployment_status}
Deployed Date: {deployed_date}

ORIGINAL EXPERIMENTAL PLAN:
{experimental_plan}

SIMULATION PREDICTIONS:
{simulation_result}

CASH FLOW ANALYSIS:
{cashflow_analysis}

ACTUAL RESULTS DATA:
Note: Since this is a summarizer for completed experiments, in a real implementation this would include:
- Actual revenue and usage metrics
- Customer feedback and behavior data  
- Operational metrics and challenges
- Competitive responses observed
- Support ticket volumes and themes
- Sales team feedback

TASK:
Analyze the pricing experiment results and provide comprehensive feedback summary. Compare actual outcomes to original predictions and provide strategic recommendations.

Focus on:
1. How well the experiment performed vs expectations
2. Key learnings about customer behavior and market dynamics
3. Financial impact and ROI of the experiment
4. Strategic implications for future pricing decisions
5. Specific recommendations for next steps

Provide both quantitative analysis and qualitative insights where available.
"""

    response = await client.responses.create(
        model="gpt-5",
        instructions=system_prompt,
        input=user_prompt,
        reasoning={"effort": "high"},
        max_output_tokens=4000,
        truncation="auto"
    )

    output_text = response.output_text or ""
    
    try:
        parsed_result = json.loads(output_text)
        return parsed_result
    except json.JSONDecodeError:
        return {"feedback_analysis": output_text, "parsing_error": "Could not parse structured output"}


async def invoke_orchestrator_async(experiments: List[PricingExperimentPydantic]) -> List[PricingExperimentPydantic]:
    tasks = [invoke_agent(experiment) for experiment in experiments]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    for idx, result in enumerate(results):
        if isinstance(result, Exception):
            experiments[idx].experiment_feedback_summary = f"Error analyzing experiment feedback: {str(result)}"
        else:
            if isinstance(result, dict):
                experiments[idx].experiment_feedback_summary = json.dumps(result, indent=2)
            else:
                experiments[idx].experiment_feedback_summary = str(result)
        
        experiments[idx].experiment_gen_stage = ExperimentGenStage.FEEDBACK_COLLECTED
    
    return experiments


def invoke_orchestrator(experiments: List[PricingExperimentPydantic]) -> List[PricingExperimentPydantic]:
    return asyncio.run(invoke_orchestrator_async(experiments))
