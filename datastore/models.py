from mongoengine import URLField, DateTimeField, FloatField, BooleanField
from mongoengine import Document, StringField, ListField, ReferenceField
from mongoengine import IntField, EmbeddedDocument, EmbeddedDocumentListField

class CustomerSegment(Document):
    segment_name = StringField()
    segment_cdp_uid = StringField()
    segment_description = StringField()
    segment_filter_logic = StringField()
    segment_usage_summary = StringField()
    segment_revenue_attribution_summary = StringField()


class Competitors(Document):
    name = StringField()
    url = URLField()
    background_research_docs = ListField(URLField())
    competitor_vs_id = StringField()

class Product(Document):
    product_name = StringField()
    product_industry = StringField()
    product_description = StringField()
    product_icp_summary = StringField()
    product_categories = ListField(URLField())
    product_categories_vs_id = StringField()
    product_feature_docs = ListField(URLField())
    product_feature_docs_vs_id = StringField()
    product_marketing_docs = ListField(URLField())
    product_marketing_docs_vs_id = StringField()
    product_technical_docs = ListField(URLField())
    product_technical_docs_vs_id = StringField()
    product_usage_docs = ListField(URLField())
    product_usage_docs_vs_id = StringField()
    product_competitors = EmbeddedDocumentListField(Competitors)
    

class TsObject(EmbeddedDocument):
    usage_value_in_units = FloatField()
    usage_unit = StringField()
    target_date = DateTimeField()

class PricingExperimentRequest(Document):
    product = ReferenceField(Product)
    experiment_number = IntField()
    objective = StringField()
    usecase = StringField()
    experiment_gen_stage = StringField(
        choices=[
            "product_context_initialized", "segments_loaded", "positioning_usage_analysis_done",
            "roi_gap_analyzer_run", "experimental_plan_generated", "simulations_run",
            "scenario_builder_completed", "cashflow_feasibility_runs_completed",
            "completed", "deployed", "feedback_collected"
        ]
    )
    created_on = DateTimeField()

class PricingExperimentRuns(Document):
    experiment_request = ReferenceField(PricingExperimentRequest, required=True)
    experiment_gen_stage = StringField(
        choices=[
            "product_context_initialized", "segments_loaded", "positioning_usage_analysis_done",
            "roi_gap_analyzer_run", "experimental_plan_generated", "simulations_run",
            "scenario_builder_completed", "cashflow_feasibility_runs_completed",
            "deployed", "feedback_collected"
        ]
    )
    product_seed_context = StringField()
    positioning_summary = StringField()
    usage_summary = StringField()
    roi_gaps = StringField()
    experimental_pricing_plan = StringField()
    simulation_result = StringField()
    usage_projections = EmbeddedDocumentListField(TsObject)
    revenue_projections = EmbeddedDocumentListField(TsObject)
    cashflow_feasibility_comments = StringField()
    experiment_feedback_summary = StringField()
    relevant_segments = ListField(ReferenceField(CustomerSegment))
    cashflow_no_negative_impact_approval_given = BooleanField()
    experiment_is_deployed = BooleanField(default=False)
    experiment_deployed_on = DateTimeField()
    created_on = DateTimeField()
