experimental_pricing_recommendation_prompt = """
Background:
You are an expert pricing analyst for 

Task:

"""

product_deep_research_prompt = """
You are supposed to be doing deep research on {product_name} offers the following features to customers:
{features}

The ICP for the product is {icp_description}

You are trying to collect as much information as possible about the product's features. In case there are additional plugins that go over the product to enhance its functionality, study them as well. If the usecase 
"""

roi_prompt = """
You are analyzing segment-wise ROI for a product. Use the provided product research context to guide what factors matter for ROI across segments.

Return a concise, table-like text with rows per segment and columns: Segment, Key Drivers, Usage Patterns, Monetization Opportunities, Risks.
"""

rabbithole_think_prompt = """
You are a rabbit hole thinker. You are given a task and you need to think about it and come up with a plan to solve the task.
"""

value_capture_analysis_prompt = """
"""

pricing_analysis_system_prompt = """
You produce clear pricing forecasts.
"""

pricing_analysis_parse_prompt = """
Parse the following into the schema.
"""

parse_into_schema_prompt = """
Please parse the following text into the given schema
"""

