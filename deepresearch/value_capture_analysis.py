from utils.openai_client import openai_client, litellm_client
from .prompts import rabbithole_think_prompt, value_capture_analysis_prompt
 

tools = [
    {
        "type": "function",
        "function": {
            "name": "go_down_rabbithole",
            "description": "Go down the rabbithole and think deeply about a particular aspect of this task only.",
            "parameters": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "hypothesis": { "type": "string", "description": "Product identifier" }
                },
                "required": ["hypothesis"]
            }
        }
    }
]

def go_down_rabbithole(hypothesis: str):
    thoughts = openai_client.responses.create(
        model="gpt-5",
        instructions=rabbithole_think_prompt,
        input=hypothesis,
        reasoning={"effort": "high"}
    )
    return thoughts.output_text

def agent(segment_roi_analysis, pricing_analysis, product_research, pricing_objective=None):
    thoughts = openai_client.responses.create(
        model="gpt-5",
        instructions=value_capture_analysis_prompt,
        input=f"## Product Research Context\n{product_research}\n\n----------------------------------\n\n## Segment-wise ROI analysis for customer\n{segment_roi_analysis}\n\n----------------------------------\n\n## Pricing Analysis Report\n{pricing_analysis}" + (f"\n\n----------------------------------\n\n## Pricing Objective\n{pricing_objective}" if pricing_objective else ""),
        reasoning={"effort": "high", "summary": "detailed"},
        truncation="auto",
        tools=[
            {
                "type": "code_interpreter",
                "container": {"type": "auto"}
            }
        ]
    )
    return thoughts.output_text