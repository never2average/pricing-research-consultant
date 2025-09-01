import os
import csv
import json
from mongoengine import connect

from datastore.models import Product, ProductPricingModel, CustomerSegment, PricingPlanSegmentContribution, CustomerUsageAnalysis, ProductPricingMapping, OrchestrationResult, Competitors



def connect_db():
    mongo_uri = os.getenv("MONGODB_URI", "mongodb://localhost:27017/pricing-research")
    connect(host=mongo_uri, alias="default")

def normalize_collection_name(name):
    if not name:
        return None
    s = name.strip().lower().replace("_", "").replace("-", "")
    if s.endswith("s"):
        s = s[:-1]
    return s


MODEL_MAP = {
    "product": Product,
    "productpricingmodel": ProductPricingModel,
    "productpricingmapping": ProductPricingMapping,
    "pricingplansegmentcontribution": PricingPlanSegmentContribution,
    "customersegment": CustomerSegment,
    "customerusageanalysis": CustomerUsageAnalysis,
    "orchestrationresult": OrchestrationResult,
}


def create_pricing_plan_segment_contribution(product, segment, pricing_model, d=None):
    number_active = 0
    number_forecast = 0
    if d:
        try:
            number_active = int(d.get("number_of_active_subscriptions", 0) or 0)
        except Exception:
            number_active = 0
        try:
            number_forecast = int(d.get("number_of_active_subscriptions_forecast", 0) or 0)
        except Exception:
            number_forecast = 0

    contribution = PricingPlanSegmentContribution(
        product=product,
        customer_segment=segment,
        pricing_plan=pricing_model,
        number_of_active_subscriptions=number_active,
        number_of_active_subscriptions_forecast=number_forecast,
        revenue_ts_data=[],
        revenue_forecast_ts_data=[],
    )
    contribution.save()
    return contribution


def create_product_from_dict(d):
    competitors_data = d.get("competitors", []) or []
    competitors_list = []
    for c in competitors_data:
        try:
            if not isinstance(c, dict):
                continue
            comp = Competitors(
                competitor_name=c.get("competitor_name"),
                website_url=c.get("website_url"),
                product_description=c.get("product_description", ""),
            )
            competitors_list.append(comp)
        except Exception:
            continue

    product = Product(
        name=d.get("name"),
        icp_description=d.get("icp_description", ""),
        unit_level_cogs=d.get("unit_level_cogs", ""),
        features_description_summary=d.get("features_description_summary", ""),
        product_documentations=d.get("product_documentations", []) or [],
        competitors=competitors_list,
    )
    product.save()
    return product


def create_pricing_model_from_dict(d):
    pricing_model = ProductPricingModel(
        plan_name=d.get("plan_name", ""),
        unit_price=float(d.get("unit_price", 99.0)),
        min_unit_count=int(d.get("min_unit_count", 1)),
        unit_calculation_logic=d.get("unit_calculation_logic", "per_seat"),
        min_unit_utilization_period=d.get("min_unit_utilization_period", "monthly"),
    )
    pricing_model.save()
    return pricing_model


def create_customer_segment_from_dict(product, d):
    segment = CustomerSegment(
        product=product,
        customer_segment_uid=d.get("customer_segment_uid"),
        customer_segment_name=d.get("customer_segment_name"),
        customer_segment_description=d.get("customer_segment_description", ""),
    )
    segment.save()
    return segment


def create_customer_usage_analysis_from_dict(product, segment, d):
    usage = CustomerUsageAnalysis(
        product=product,
        customer_segment=segment,
        customer_uid=d.get("customer_uid"),
        customer_task_to_agent=d.get("customer_task_to_agent", ""),
        predicted_customer_satisfaction_response=float(d.get("predicted_customer_satisfaction_response", 0.0)),
        predicted_customer_satisfaction_response_reasoning=d.get("predicted_customer_satisfaction_response_reasoning", ""),
    )
    usage.save()
    return usage


def create_product_pricing_mapping(product, pricing_model, is_active="true"):
    mapping = ProductPricingMapping(
        product=product,
        pricing_model=pricing_model,
        is_active=is_active,
    )
    mapping.save()
    return mapping


def create_from_json_file(path):
    with open(path, "r") as f:
        payload = json.load(f)

    product_data = payload.get("product", {})
    pricing_models_data = payload.get("pricing_models", [])
    customer_segments = payload.get("customer_segments", [])

    if not product_data or not product_data.get("name"):
        raise ValueError("product.name is required in JSON payload")

    if not pricing_models_data:
        raise ValueError("pricing_models array is required in JSON payload")

    product = create_product_from_dict(product_data)

    created_pricing_models = []
    pricing_model_map = {}
    for pricing_data in pricing_models_data:
        pricing_model = create_pricing_model_from_dict(pricing_data)
        pricing_model_id = str(pricing_model.id)
        pricing_model_map[pricing_model_id] = pricing_model
        created_pricing_models.append(pricing_model)

        # Create product-pricing mapping
        create_product_pricing_mapping(product, pricing_model)

    created_segments = []
    for seg in customer_segments:
        segment = create_customer_segment_from_dict(product, seg)

        pricing_model_indices = seg.get("pricing_model_ids", [])
        if not pricing_model_indices:
            pricing_model_indices = list(range(len(created_pricing_models)))

        for index in pricing_model_indices:
            if isinstance(index, int) and 0 <= index < len(created_pricing_models):
                create_pricing_plan_segment_contribution(product, segment, created_pricing_models[index], seg)
            elif isinstance(index, str) and index in pricing_model_map:
                create_pricing_plan_segment_contribution(product, segment, pricing_model_map[index], seg)

        for usage in seg.get("usage_analyses", []) or []:
            create_customer_usage_analysis_from_dict(product, segment, usage)
        created_segments.append(segment)

    return product, created_pricing_models, created_segments


def create_from_csv_file(path):
    product = None
    pricing_model = None
    segment_by_uid = {}

    with open(path, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if product is None:
                docs = row.get("product_documentations", "").strip()
                docs_list = []
                if docs:
                    sep = ";" if ";" in docs else ","
                    docs_list = [x.strip() for x in docs.split(sep) if x.strip()]

                product = create_product_from_dict({
                    "name": row.get("product_name"),
                    "icp_description": row.get("icp_description", ""),
                    "unit_level_cogs": row.get("unit_level_cogs", ""),
                    "features_description_summary": row.get("features_description_summary", ""),
                    "product_documentations": docs_list,
                })

            if pricing_model is None:
                pricing_model = create_pricing_model_from_dict({
                    "plan_name": row.get("plan_name", ""),
                    "unit_price": row.get("unit_price", 99.0),
                    "min_unit_count": row.get("min_unit_count", 1),
                    "unit_calculation_logic": row.get("unit_calculation_logic", "per_seat"),
                    "min_unit_utilization_period": row.get("min_unit_utilization_period", "monthly"),
                })
                # Create product-pricing mapping
                create_product_pricing_mapping(product, pricing_model)

            uid = row.get("customer_segment_uid")
            if not uid:
                raise ValueError("customer_segment_uid is required in CSV")

            if uid not in segment_by_uid:
                seg_dict = {
                    "customer_segment_uid": uid,
                    "customer_segment_name": row.get("customer_segment_name"),
                    "customer_segment_description": row.get("customer_segment_description", ""),
                }
                segment = create_customer_segment_from_dict(product, seg_dict)
                create_pricing_plan_segment_contribution(product, segment, pricing_model, row)
                segment_by_uid[uid] = segment

            segment = segment_by_uid[uid]

            usage_dict = {
                "customer_uid": row.get("customer_uid"),
                "customer_task_to_agent": row.get("customer_task_to_agent", ""),
                "predicted_customer_satisfaction_response": row.get("predicted_customer_satisfaction_response", 0.0),
                "predicted_customer_satisfaction_response_reasoning": row.get("predicted_customer_satisfaction_response_reasoning", ""),
            }
            if usage_dict.get("customer_uid"):
                create_customer_usage_analysis_from_dict(product, segment, usage_dict)

    created_segments = list(segment_by_uid.values())
    if product is None or pricing_model is None:
        raise ValueError("CSV did not contain product/pricing rows")
    return product, pricing_model, created_segments


def delete_one(collection_name, doc_id):
    key = normalize_collection_name(collection_name)
    Model = MODEL_MAP.get(key)
    if not Model:
        raise ValueError(f"Unknown collection: {collection_name}")
    obj = Model.objects.get(id=doc_id)
    obj.delete()
    return True


def delete_many(collection_name, ids):
    key = normalize_collection_name(collection_name)
    Model = MODEL_MAP.get(key)
    if not Model:
        raise ValueError(f"Unknown collection: {collection_name}")
    deleted = 0
    errors = []
    for i in ids:
        try:
            count = Model.objects(id=i).delete()
            if count:
                deleted += 1
            else:
                errors.append(i)
        except Exception:
            errors.append(i)
    return {"deleted": deleted, "requested": len(ids), "errors": errors}


def get_one(collection_name, doc_id):
    key = normalize_collection_name(collection_name)
    Model = MODEL_MAP.get(key)
    if not Model:
        raise ValueError(f"Unknown collection: {collection_name}")
    return Model.objects.get(id=doc_id)


def list_all_ids(collection_name):
    key = normalize_collection_name(collection_name)
    Model = MODEL_MAP.get(key)
    if not Model:
        raise ValueError(f"Unknown collection: {collection_name}")
    docs = list(Model.objects())
    return [str(d.id) for d in docs]


def _to_plain_value(v):
    try:
        if isinstance(v, (dict, list)):
            return json.dumps(v, ensure_ascii=False)
        return str(v)
    except Exception:
        try:
            return str(v)
        except Exception:
            return ""


def document_to_markdown_table(obj):
    try:
        data = obj.to_mongo().to_dict()
    except Exception:
        try:
            data = json.loads(obj.to_json())
        except Exception:
            data = {}

    lines = []
    lines.append("| field | value |")
    lines.append("|---|---|")
    for k in sorted(list(data.keys())):
        v = data.get(k)
        lines.append(f"| {k} | {_to_plain_value(v)} |")
    return "\n".join(lines)


def list_one_markdown(collection_name, doc_id):
    obj = get_one(collection_name, doc_id)
    key = normalize_collection_name(collection_name)
    if key == "product":
        return list_product_related_markdown(obj)
    return document_to_markdown_table(obj)


def list_all_markdown(collection_name):
    ids = list_all_ids(collection_name)
    norm = normalize_collection_name(collection_name) or collection_name
    lines = []
    lines.append("| collection | id |")
    lines.append("|---|---|")
    for i in ids:
        lines.append(f"| {norm} | {i} |")
    return "\n".join(lines)


def list_product_related_markdown(product):
    try:
        segs = list(CustomerSegment.objects(product=product))
    except Exception:
        segs = []
    try:
        contribs = list(PricingPlanSegmentContribution.objects(product=product))
    except Exception:
        contribs = []

    pricing_ids = []
    seen = set()
    for c in contribs:
        try:
            pid = str(c.pricing_plan.id) if c.pricing_plan else None
        except Exception:
            pid = None
        if pid and pid not in seen:
            seen.add(pid)
            pricing_ids.append(pid)

    lines = []
    lines.append(document_to_markdown_table(product))

    if segs:
        lines.append("")
        lines.append("| customer_segment_id |")
        lines.append("|---|")
        for s in segs:
            try:
                lines.append(f"| {str(s.id)} |")
            except Exception:
                continue

    if pricing_ids:
        lines.append("")
        lines.append("| pricing_model_id |")
        lines.append("|---|")
        for pid in pricing_ids:
            lines.append(f"| {pid} |")

    return "\n".join(lines)
