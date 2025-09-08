from pydantic import BaseModel
from typing import List


class LLMsIntegratorPrimer(BaseModel):
    llms_txt_context: str
    llms_txt_cover_text: str
    env_vars: List[str]


def generate_llms_integrator_primer(product_tool, customer_tool, revenue_tool):
    # Generate integrated platform configuration
    llms_txt_context = f"""# Integrated Platform Configuration

## Overview
This configuration enables multi-platform integration for comprehensive pricing research and analytics.

## Integrated Tools
- **Product Analytics**: {product_tool}
- **Customer Data Platform**: {customer_tool}  
- **Revenue Management**: {revenue_tool}

## Data Sources
- Product analytics and user behavior data
- Customer data platform insights
- Revenue and subscription metrics
- Real-time analytics and metrics
- Historical data analysis capabilities

## Data Integration Flow
1. Product data from {product_tool}
2. Customer insights from {customer_tool}
3. Revenue metrics from {revenue_tool}
4. Combined analytics for comprehensive pricing research

## Usage
1. Configure connections for all integrated tools
2. Set up unified data pipelines
3. Run comprehensive pricing analysis experiments
"""
    
    llms_txt_cover_text = f"""Integrated platform configuration guide - Multi-tool data integration for pricing research platform."""
    
    # Generate environment variables for all tools
    product_vars = [
        f"{product_tool.upper().replace(' ', '_')}_API_KEY",
        f"{product_tool.upper().replace(' ', '_')}_PROJECT_ID",
        f"{product_tool.upper().replace(' ', '_')}_TRACKING_ID"
    ]
    
    customer_vars = [
        f"{customer_tool.upper().replace(' ', '_')}_API_KEY",
        f"{customer_tool.upper().replace(' ', '_')}_WORKSPACE_ID",
        f"{customer_tool.upper().replace(' ', '_')}_SOURCE_ID"
    ]
    
    revenue_vars = [
        f"{revenue_tool.upper().replace(' ', '_')}_API_KEY",
        f"{revenue_tool.upper().replace(' ', '_')}_SECRET_KEY",
        f"{revenue_tool.upper().replace(' ', '_')}_WEBHOOK_SECRET"
    ]
    
    # Add general integration config vars
    integration_vars = [
        "INTEGRATED_PLATFORM_CONFIG",
        "PLATFORM_BASE_URL",
        "INTEGRATION_CONFIG_PATH",
        "DATA_SYNC_INTERVAL"
    ]
    
    env_vars = product_vars + customer_vars + revenue_vars + integration_vars
    
    return LLMsIntegratorPrimer(
        llms_txt_context=llms_txt_context,
        llms_txt_cover_text=llms_txt_cover_text,
        env_vars=env_vars
    )
