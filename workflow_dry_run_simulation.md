# Pricing Research Workflow - Dry Run Simulation

## Initial Input
```json
{
  "experiment_id": "exp_001",
  "objective": "Increase revenue from enterprise customers by testing value-based pricing",
  "usecase": "SaaS platform wants to optimize pricing for enterprise segment",
  "product": {
    "product_name": "DataFlow Analytics",
    "product_description": "Enterprise data analytics and visualization platform",
    "product_industry": "SaaS/Data Analytics",
    "product_icp_summary": "Mid-market to enterprise companies with 500+ employees needing advanced data insights",
    "product_categories": ["Analytics", "Business Intelligence", "Data Visualization"],
    "product_marketing_docs_vs_id": "vs_marketing_123",
    "product_feature_docs_vs_id": "vs_features_456",
    "product_technical_docs_vs_id": "vs_technical_789",
    "product_usage_docs_vs_id": "vs_usage_101",
    "product_competitors": {
      "name": "Tableau, PowerBI, Looker",
      "competitor_vs_id": "vs_competitors_202"
    }
  },
  "experiment_gen_stage": null
}
```

---

## Stage 1: Product Research Agent
**Input**: Initial experiment data
**Processing**: Analyzes product documentation using vector stores
**Output**:

```json
{
  "product_seed_context": "DataFlow Analytics is an enterprise-grade data analytics platform that serves mid-market to enterprise companies (500+ employees). The platform offers advanced data visualization capabilities, real-time dashboard creation, and predictive analytics features. 

Key differentiators:
- Advanced ML-powered insights engine
- Enterprise-grade security and compliance (SOC2, GDPR, HIPAA)
- Custom white-label solutions for large enterprises
- API-first architecture enabling seamless integrations
- Dedicated customer success management for enterprise accounts

Current pricing model appears to be seat-based with three tiers:
- Professional: $49/user/month (up to 100 users)
- Enterprise: $99/user/month (unlimited users, advanced features)
- Custom: Enterprise pricing for 1000+ users

Target customers typically have complex data infrastructure needs, require advanced security features, and value custom integrations. Usage patterns show heavy utilization during business hours with peak usage during month-end reporting cycles.",

  "experiment_gen_stage": "PRODUCT_CONTEXT_INITIALIZED"
}
```

---

## Stage 2: Segment Research Agent
**Input**: Product context + available customer segments
**Processing**: Analyzes which customer segments are best fit for pricing experiment
**Output**: Creates multiple experiment variants (one per selected segment)

### Experiment 1A - Enterprise Segment
```json
{
  "relevant_segment": {
    "segment_name": "Enterprise Heavy Users",
    "segment_description": "Large companies (1000+ employees) with high data processing needs",
    "segment_usage_summary": "Average 150 active users, 500GB+ data processing monthly, requires advanced security features, custom integrations, and dedicated support. Typical contract value $180K-$500K annually."
  },
  "experiment_gen_stage": "SEGMENTS_LOADED"
}
```

### Experiment 1B - Mid-Market Segment  
```json
{
  "relevant_segment": {
    "segment_name": "Mid-Market Growth Companies",
    "segment_description": "Fast-growing companies (500-1000 employees) scaling their data operations", 
    "segment_usage_summary": "Average 75 active users, 200GB data processing monthly, growing rapidly, price-sensitive but value advanced features. Typical contract value $60K-$180K annually."
  },
  "experiment_gen_stage": "SEGMENTS_LOADED"
}
```

---

## Stage 3: Marketing Material Agent (Parallel with others)
**Input**: Product seed context + vector stores
**Processing**: Analyzes positioning and usage patterns
**Output**:

```json
{
  "positioning_summary": "DataFlow Analytics positions itself as the 'Enterprise Data Platform for Intelligent Decision Making.' Key positioning pillars: (1) Advanced AI/ML insights that go beyond basic reporting (2) Enterprise-grade security and compliance for regulated industries (3) Scalable architecture that grows with customer needs (4) Customer success partnership model vs. self-service competitors.",

  "usage_summary": "Enterprise customers primarily use DataFlow for: Monthly/quarterly business reviews (peak usage), Real-time operational dashboards (consistent daily usage), Predictive analytics for forecasting (weekly cycles), Custom reporting for stakeholders (ad-hoc spikes). Usage patterns show 70% business users, 30% technical users, with heaviest usage during business hours EST.",

  "experiment_gen_stage": "POSITIONING_USAGE_ANALYSIS_DONE"
}
```

---

## Stage 4: Competitor Research Agent (Parallel)
**Input**: Product seed context + competitor data
**Processing**: Benchmarks competitive pricing and positioning  
**Output**:

```json
{
  "competitive_analysis": {
    "competitor_landscape": "Highly competitive market with Tableau (40% market share), Microsoft PowerBI (25%), and Looker/Google (15%). DataFlow competes primarily on advanced ML capabilities and enterprise security.",
    
    "pricing_model_analysis": {
      "tableau": "Seat-based: Creator ($70/month), Explorer ($42/month), Viewer ($15/month)",
      "powerbi": "Per-user: Pro ($10/month), Premium ($20/month), embedded pricing available", 
      "looker": "Platform pricing: $3000-5000/month base + per-user fees",
      "dataflow": "Current: $49-99/user, Custom enterprise pricing"
    },
    
    "competitive_gaps": "DataFlow has opportunity to differentiate on: (1) Value-based pricing tied to data volume/insights generated (2) Outcome-based pricing models (3) Industry-specific pricing packages",
    
    "strategic_recommendations": "Consider usage-based pricing to compete with PowerBI's low per-user cost while capturing value from high-usage enterprise customers. Premium ML features could command 40-60% price premium over basic competitors."
  }
}
```

---

## Stage 5: ROI Gap Analyzer  
**Input**: Product context + segment data + competitive intelligence
**Processing**: Identifies revenue optimization opportunities
**Output**:

```json
{
  "roi_gaps": {
    "current_roi_assessment": "DataFlow captures ~60% of potential value. Current seat-based model undervalues heavy usage customers and overprices light users.",
    
    "identified_gaps": [
      {
        "gap": "High-usage customers paying same per-seat rate as light users",
        "impact": "$200K-500K annual revenue potential per enterprise account"
      },
      {
        "gap": "Advanced ML features bundled in standard pricing", 
        "impact": "$50-100/user/month premium pricing opportunity"
      },
      {
        "gap": "No pricing differentiation for industry-specific needs",
        "impact": "15-25% price premium for regulated industries"
      }
    ],
    
    "priority_recommendations": [
      "Implement usage-based pricing tiers for data processing volume",
      "Create premium ML/AI feature tier with outcome-based pricing",
      "Develop industry-specific packages for healthcare, finance, retail"
    ],
    
    "quantified_impact_ranges": "Conservative: +15% revenue ($2.5M annually), Optimistic: +35% revenue ($6M annually)"
  },
  "experiment_gen_stage": "ROI_GAP_ANALYZER_RUN"
}
```

---

## Stage 6: Experimental Pricing Generator
**Input**: Product context + ROI gaps + segment data
**Processing**: Designs specific pricing experiment
**Output**:

```json
{
  "experimental_pricing_plan": {
    "experiment_hypothesis": "Enterprise customers will accept 25-35% price increase if pricing aligns with their actual usage patterns and includes premium ML features",
    
    "pricing_model_design": {
      "base_tier": "$75/user/month (was $99) - Core analytics features",
      "usage_multiplier": "+$0.10 per GB data processed above 100GB baseline", 
      "ml_premium": "+$40/user/month - Advanced ML insights, predictive analytics",
      "enterprise_add_ons": "Custom integrations: $5K setup + $1K/month, Dedicated CSM: $3K/month"
    },
    
    "test_parameters": {
      "sample_size": "50 enterprise accounts (25 control, 25 treatment)",
      "duration": "6 months with monthly review gates",
      "success_metrics": ["Revenue per account (+20% target)", "Churn rate (<5%)", "Feature adoption (ML features 60%+)"]
    },
    
    "expected_outcomes": {
      "conservative": "10-15% revenue increase, 2-3% churn increase",
      "optimistic": "25-35% revenue increase, churn neutral"
    }
  },
  "experiment_gen_stage": "EXPERIMENTAL_PLAN_GENERATED"
}
```

---

## Stage 7: Invoke Simulations Agent
**Input**: Experimental pricing plan + product context
**Processing**: Runs multiple scenario simulations
**Output**:

```json
{
  "simulation_result": {
    "baseline_projections": {
      "current_monthly_revenue": "$850K",
      "current_churn_rate": "4%",
      "current_expansion_rate": "12%"
    },
    
    "experimental_projections": {
      "pessimistic": {
        "revenue_change": "+8%", 
        "churn_impact": "+2%",
        "monthly_revenue_forecast": "$918K"
      },
      "realistic": {
        "revenue_change": "+22%",
        "churn_impact": "+1%", 
        "monthly_revenue_forecast": "$1,037K"
      },
      "optimistic": {
        "revenue_change": "+33%",
        "churn_impact": "0%",
        "monthly_revenue_forecast": "$1,131K"
      }
    },
    
    "confidence_intervals": "70% confidence in 15-30% revenue increase range"
  },
  
  "usage_projections": [
    {"usage_value_in_units": 1200, "usage_unit": "active_users", "target_date": "2024-01-01"},
    {"usage_value_in_units": 1250, "usage_unit": "active_users", "target_date": "2024-02-01"}
  ],
  
  "revenue_projections": [
    {"usage_value_in_units": 1037000, "usage_unit": "projected_revenue_usd", "target_date": "2024-01-01"},
    {"usage_value_in_units": 1089000, "usage_unit": "projected_revenue_usd", "target_date": "2024-02-01"}
  ],
  
  "experiment_gen_stage": "SIMULATIONS_RUN"
}
```

---

## Stage 8: Scenario Builder Agent (Parallel with simulations)
**Input**: Pricing plan + simulation results
**Processing**: Creates comprehensive scenario matrix
**Output**:

```json
{
  "scenario_analysis": {
    "baseline_scenario": "Market conditions remain stable, competitors don't respond aggressively to pricing changes",
    
    "optimistic_scenario": {
      "conditions": "Strong economy, high customer growth, successful ML feature adoption",
      "probability": "25%",
      "revenue_impact": "+40-50% from baseline"
    },
    
    "pessimistic_scenario": {
      "conditions": "Economic downturn, aggressive competitor pricing, customer budget cuts",
      "probability": "20%", 
      "revenue_impact": "-10 to +5% from baseline"
    },
    
    "black_swan_scenarios": ["Major competitor launches free tier", "Economic recession causes 30% customer churn", "New regulation changes data analytics requirements"],
    
    "monitoring_indicators": ["Customer pricing objections increase >15%", "Competitor pricing moves", "Usage pattern changes", "Feature adoption rates"],
    
    "contingency_plans": {
      "if_churn_exceeds_7%": "Implement 3-month pricing freeze and enhanced customer success outreach",
      "if_competitor_undercuts": "Activate value-based messaging campaign and custom negotiation guidelines"
    }
  },
  "experiment_gen_stage": "SCENARIO_BUILDER_COMPLETED"
}
```

---

## Stage 9: CashFlow Feasibility Analyzer
**Input**: Pricing plan + simulations + projections
**Processing**: Financial impact and feasibility analysis
**Output**:

```json
{
  "cashflow_feasibility_comments": {
    "cash_flow_summary": "Experiment shows positive cash flow impact within 3 months. Break-even on implementation costs achieved in month 2.",
    
    "monthly_projections": [
      {"month": 1, "incremental_revenue": "$45K", "implementation_costs": "$25K", "net_impact": "$20K"},
      {"month": 2, "incremental_revenue": "$125K", "implementation_costs": "$10K", "net_impact": "$115K"},
      {"month": 3, "incremental_revenue": "$187K", "implementation_costs": "$5K", "net_impact": "$182K"}
    ],
    
    "investment_requirements": {
      "system_changes": "$35K one-time",
      "sales_training": "$15K",
      "customer_communication": "$10K",
      "ongoing_monitoring": "$5K/month"
    },
    
    "risk_assessment": "Low financial risk. Worst-case scenario still shows positive ROI within 6 months. Main risk is customer churn exceeding 7%.",
    
    "approval_recommendation": "PROCEED - Strong financial case with acceptable risk profile. Recommend 6-month pilot with monthly review gates."
  },
  
  "cashflow_no_negative_impact_approval_given": true,
  "experiment_gen_stage": "CASHFLOW_FEASIBILITY_RUNS_COMPLETED"
}
```

---

## Stage 10: Experiment Feedback Summarizer
**Input**: Complete experiment plan + simulations + cashflow analysis
**Processing**: Strategic analysis and recommendations
**Output**:

```json
{
  "experiment_feedback_summary": {
    "experiment_summary": "Value-based pricing experiment targeting enterprise segment with usage-based components and ML premium features. Projected 22% revenue increase with manageable risk profile.",
    
    "hypothesis_validation": "Hypothesis partially validated by simulations - customers likely to accept pricing changes due to value alignment, though churn risk exists.",
    
    "key_metrics_performance": {
      "revenue_target": "20% increase - LIKELY TO EXCEED (22% projected)",
      "churn_target": "<5% - AT RISK (simulation shows 5-6%)",
      "feature_adoption": "60% ML adoption - ACHIEVABLE based on usage patterns"
    },
    
    "strategic_implications": [
      "Value-based pricing model validates product's premium positioning",
      "Usage-based components align pricing with customer success",
      "ML premium tier creates clear upgrade path and revenue expansion"
    ],
    
    "recommendations": [
      "Proceed with 6-month pilot on 50 enterprise accounts",
      "Implement enhanced customer success for treatment group",
      "Develop competitive response plan for potential pricing wars",
      "Create customer communication framework highlighting value alignment"
    ],
    
    "confidence_level": "High confidence (75%) in positive financial outcome based on comprehensive analysis"
  },
  "experiment_gen_stage": "FEEDBACK_COLLECTED"
}
```

---

## Final State Summary

**Total Processing Time**: ~45 minutes (parallel execution where possible)
**Experiment Variants Created**: 2 (Enterprise Heavy Users, Mid-Market Growth)
**Key Decision**: ✅ PROCEED with pricing experiment
**Financial Projection**: +22% revenue increase ($187K additional monthly revenue)
**Risk Level**: Low-Medium (manageable with monitoring)
**Next Step**: Deploy experiment to 50 enterprise accounts for 6-month pilot

**Fields Populated**: 15 fields across the full PricingExperimentPydantic model
**Stages Completed**: All 10 stages from initial input to feedback collection
**Ready for Deployment**: Yes, with comprehensive analysis and risk mitigation plans

---

## Orchestration Insights

1. **Parallel Processing Efficiency**: Stages 3-4 run concurrently after product_seed_context
2. **Data Dependencies**: Each agent builds on previous outputs in logical sequence  
3. **Risk Management**: Multiple validation layers (ROI → Financial → Scenario analysis)
4. **Decision Support**: Clear go/no-go recommendation with quantified projections
5. **Actionable Output**: Specific implementation plan with success metrics and monitoring

The workflow successfully transforms high-level business objectives into detailed, validated pricing experiments ready for deployment.
