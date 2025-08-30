import instructor
from litellm import completion
from utils.openai_client import openai_client
from .prompts import rabbithole_think_prompt, value_capture_analysis_prompt
 
llm_client = instructor.from_litellm(completion)


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
        instruction=rabbithole_think_prompt,
        input=hypothesis,
        reasoning={"effort": "high"}
    )
    return thoughts.output_text

def agent(segment_roi_analysis, pricing_analysis, product_research):
    thoughts = openai_client.responses.create(
        model="gpt-5",
        instruction=value_capture_analysis_prompt,
        input=f"## Product Research Context\n{product_research}\n\n----------------------------------\n\n## Segment-wise ROI analysis for customer\n{segment_roi_analysis}\n\n----------------------------------\n\n## Pricing Analysis Report\n{pricing_analysis}",
        reasoning={"effort": "high", "summary": "detailed"},
        tools=tools,
        tool_choice="auto",
        truncation="auto",
        temperature=0.2
    )
    return thoughts.output_text