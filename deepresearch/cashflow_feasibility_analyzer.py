import asyncio
import json
from typing import List
from datastore.types import PricingExperimentPydantic, ExperimentGenStage
from utils.openai_client import get_openai_client


async def invoke_agent(pricing_experiment: PricingExperimentPydantic):
    client = get_openai_client()
    
    system_prompt = """
You are a financial analyst specializing in cash flow analysis for pricing experiments. Provide comprehensive financial analysis and risk assessment for proposed pricing changes to inform deployment planning.

CASH FLOW ANALYSIS FRAMEWORK:
1. Revenue Impact Analysis - Changes in top-line revenue streams
2. Cost Structure Analysis - Impact on variable and fixed costs
3. Working Capital Analysis - Changes in payment terms, collections, inventory
4. Investment Requirements - Infrastructure, systems, personnel needs
5. Risk Assessment - Financial risks and mitigation strategies
6. Break-even Analysis - Time to positive cash flow impact
7. Sensitivity Analysis - Impact of key assumptions on cash flow

FINANCIAL METRICS TO EVALUATE:
- Monthly cash flow projections for 12-24 months
- Break-even timeline and customer acquisition requirements
- Net present value (NPV) of the pricing change
- Internal rate of return (IRR) on required investments
- Cash flow at risk (CFaR) under different scenarios
- Working capital requirements and financing needs

OUTPUT FORMAT:
Provide structured JSON with these exact keys:
- cash_flow_summary: Executive summary of financial impact
- monthly_projections: Month-by-month cash flow estimates
- break_even_analysis: Time and conditions to reach break-even
- investment_requirements: Upfront and ongoing investment needs
- risk_assessment: Financial risks and probability-weighted impacts
- sensitivity_analysis: Key variables that most affect cash flow
- financing_needs: Any external financing requirements
- approval_recommendation: Analysis summary with risk assessment and recommended precautions
- key_assumptions: Critical financial assumptions made

REQUIREMENTS:
- Provide specific dollar amounts and timeframes
- Include confidence intervals for key projections
- Consider both optimistic and conservative scenarios
- Account for implementation costs and operational changes
- Flag any cash flow risks and recommend monitoring strategies
- Focus on risk mitigation and financial planning guidance
"""

    product_name = pricing_experiment.product.product_name if pricing_experiment.product else "Unknown Product"
    experimental_plan = pricing_experiment.experimental_pricing_plan or "No pricing plan available"
    simulation_result = pricing_experiment.simulation_result or "No simulation data available"
    usage_projections = pricing_experiment.usage_projections or []
    revenue_projections = pricing_experiment.revenue_projections or []
    objective = pricing_experiment.objective or "Not specified"
    usecase = pricing_experiment.usecase or "Not specified"

    user_prompt = f"""
CONTEXT:
Product: {product_name}
Experiment Objective: {objective}  
Use Case: {usecase}

EXPERIMENTAL PRICING PLAN:
{experimental_plan}

3-SCENARIO SIMULATION RESULTS:
{simulation_result}

USAGE PROJECTIONS:
{json.dumps([{"value": proj.usage_value_in_units, "unit": proj.usage_unit, "date": proj.target_date.isoformat() if proj.target_date else None} for proj in usage_projections], indent=2) if usage_projections else "No usage projections available"}

REVENUE PROJECTIONS:
{json.dumps([{"value": proj.usage_value_in_units, "unit": proj.usage_unit, "date": proj.target_date.isoformat() if proj.target_date else None} for proj in revenue_projections], indent=2) if revenue_projections else "No revenue projections available"}

TASK:
Conduct a comprehensive cash flow feasibility analysis for the proposed pricing experiment using the 3-scenario simulation results (Conservative, Realistic, Optimistic). Evaluate the financial viability, cash flow impact, and investment requirements across all scenarios.

Focus on:
1. Monthly cash flow projections for all 3 scenarios with confidence intervals
2. Break-even timeline and requirements under different scenarios
3. Investment needs and financing requirements across scenarios
4. Risk factors that could impact cash flow in each scenario
5. Financial risk assessment with recommended precautions and monitoring
6. Which scenario(s) to prepare for financially and contingency planning

Provide specific financial metrics for each scenario and highlight any cash flow concerns that need immediate attention. The analysis will inform deployment planning but will not block the experiment from proceeding.
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
        
        approval_recommendation = parsed_result.get("approval_recommendation", "")
        no_negative_impact = True  # Always approve - remove rejection scenario
        
        # Log the original recommendation for analysis purposes but don't block workflow
        original_recommendation = ""
        if isinstance(approval_recommendation, str):
            original_recommendation = approval_recommendation
        elif isinstance(approval_recommendation, dict):
            original_recommendation = str(approval_recommendation)
        
        return {
            "cashflow_analysis": parsed_result,
            "no_negative_impact_approval": no_negative_impact,
            "original_recommendation": original_recommendation
        }
        
    except json.JSONDecodeError:
        return {"cashflow_analysis": output_text, "parsing_error": "Could not parse structured output"}


async def invoke_orchestrator_async(experiments: List[PricingExperimentPydantic]) -> List[PricingExperimentPydantic]:
    tasks = [invoke_agent(experiment) for experiment in experiments]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    for idx, result in enumerate(results):
        if isinstance(result, Exception):
            experiments[idx].cashflow_feasibility_comments = f"Error in cash flow analysis: {str(result)}"
            experiments[idx].cashflow_no_negative_impact_approval_given = True  # Always approve - no blocking
        else:
            if isinstance(result, dict):
                cashflow_data = result.get("cashflow_analysis", result)
                experiments[idx].cashflow_feasibility_comments = json.dumps(cashflow_data, indent=2)
                experiments[idx].cashflow_no_negative_impact_approval_given = True  # Always approve - no blocking
            else:
                experiments[idx].cashflow_feasibility_comments = str(result)
                experiments[idx].cashflow_no_negative_impact_approval_given = True  # Always approve - no blocking
        
        experiments[idx].experiment_gen_stage = ExperimentGenStage.CASHFLOW_FEASIBILITY_RUNS_COMPLETED
    
    return experiments


def invoke_orchestrator(experiments: List[PricingExperimentPydantic]) -> List[PricingExperimentPydantic]:
    return asyncio.run(invoke_orchestrator_async(experiments))
