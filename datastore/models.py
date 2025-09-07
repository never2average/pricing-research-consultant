# pyright: reportUnknownParameterType=false, reportUnknownArgumentType=false, reportUnknownVariableType=false, reportMissingParameterType=false, reportReturnType=false
# ruff: noqa: ANN,ANN001,ANN201
import os
import asyncio
import threading
import tempfile
from urllib.parse import urlparse
import httpx
from mongoengine import URLField, DateTimeField, FloatField, BooleanField
from mongoengine import Document, StringField, ListField, ReferenceField
from mongoengine import IntField, EmbeddedDocument, EmbeddedDocumentListField
from utils.openai_client import get_openai_client
from mongoengine import signals

class CustomerSegment(Document):
    segment_name = StringField()
    segment_cdp_uid = StringField()
    segment_description = StringField()
    segment_filter_logic = StringField()
    segment_usage_summary = StringField()
    segment_revenue_attribution_summary = StringField()


class Competitors(EmbeddedDocument):
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
    relevant_segment = ReferenceField(CustomerSegment)
    cashflow_no_negative_impact_approval_given = BooleanField()
    experiment_is_deployed = BooleanField(default=False)
    experiment_deployed_on = DateTimeField()
    created_on = DateTimeField()


async def reset_vector_store(file_paths, existing_vector_store_id=None, name=None, also_delete_files=True):
    client = get_openai_client()
    if existing_vector_store_id:
        files = await client.vector_stores.files.list(vector_store_id=existing_vector_store_id)
        ids = [f.id for f in getattr(files, "data", [])]
        for fid in ids:
            try:
                await client.vector_stores.files.delete(vector_store_id=existing_vector_store_id, file_id=fid)
            except Exception:
                pass
        if also_delete_files:
            for fid in ids:
                try:
                    await client.files.delete(file_id=fid)
                except Exception:
                    pass
        try:
            await client.vector_stores.delete(existing_vector_store_id)
        except Exception:
            pass

    uploaded_file_ids = []
    tmp_dir = None
    tmp_paths = []
    try:
        paths = file_paths or []
        for path in paths:
            is_url = isinstance(path, str) and (path.startswith("http://") or path.startswith("https://"))
            local_path = path
            if is_url:
                if tmp_dir is None:
                    tmp_dir = tempfile.mkdtemp(prefix="vs_upload_")
                try:
                    async with httpx.AsyncClient(follow_redirects=True, timeout=60.0) as ac:
                        r = await ac.get(path)
                        if r.status_code == 200:
                            parsed = urlparse(path)
                            name_guess = os.path.basename(parsed.path) or "downloaded_file"
                            local_path = os.path.join(tmp_dir, name_guess)
                            with open(local_path, "wb") as out:
                                out.write(r.content)
                            tmp_paths.append(local_path)
                        else:
                            local_path = None
                except Exception:
                    local_path = None
            if not local_path:
                continue
            try:
                with open(local_path, "rb") as fh:
                    res = await client.files.create(file=fh, purpose="assistants")
                    if getattr(res, "id", None):
                        uploaded_file_ids.append(res.id)
            except Exception:
                pass
    finally:
        if tmp_paths:
            for p in tmp_paths:
                try:
                    os.remove(p)
                except Exception:
                    pass
        if tmp_dir:
            try:
                os.rmdir(tmp_dir)
            except Exception:
                pass

    vs = await client.vector_stores.create(name=name or "Research Docs")
    for fid in uploaded_file_ids:
        try:
            await client.vector_stores.files.create(vector_store_id=vs.id, file_id=fid)
        except Exception:
            pass
    return {"vector_store_id": vs.id, "file_ids": uploaded_file_ids}


def _schedule_coro(coro):
    try:
        loop = asyncio.get_running_loop()
        loop.create_task(coro)
    except RuntimeError:
        def _runner():
            asyncio.run(coro)
        t = threading.Thread(target=_runner, daemon=True)
        t.start()


async def rebuild_product_vector_stores(product):
    client = get_openai_client()
    updates = {}

    try:
        docs = product.product_marketing_docs or []
        vs_id = product.product_marketing_docs_vs_id
        if docs:
            res = await reset_vector_store(docs, existing_vector_store_id=vs_id, name=f"Marketing Docs: {product.product_name}")
            updates["set__product_marketing_docs_vs_id"] = res.get("vector_store_id")
        elif vs_id:
            try:
                await client.vector_stores.delete(vs_id)
            except Exception:
                pass
            updates["set__product_marketing_docs_vs_id"] = None
    except Exception:
        pass

    try:
        docs = product.product_feature_docs or []
        vs_id = product.product_feature_docs_vs_id
        if docs:
            res = await reset_vector_store(docs, existing_vector_store_id=vs_id, name=f"Feature Docs: {product.product_name}")
            updates["set__product_feature_docs_vs_id"] = res.get("vector_store_id")
        elif vs_id:
            try:
                await client.vector_stores.delete(vs_id)
            except Exception:
                pass
            updates["set__product_feature_docs_vs_id"] = None
    except Exception:
        pass

    try:
        docs = product.product_technical_docs or []
        vs_id = product.product_technical_docs_vs_id
        if docs:
            res = await reset_vector_store(docs, existing_vector_store_id=vs_id, name=f"Technical Docs: {product.product_name}")
            updates["set__product_technical_docs_vs_id"] = res.get("vector_store_id")
        elif vs_id:
            try:
                await client.vector_stores.delete(vs_id)
            except Exception:
                pass
            updates["set__product_technical_docs_vs_id"] = None
    except Exception:
        pass

    try:
        docs = product.product_categories or []
        vs_id = product.product_categories_vs_id
        if docs:
            res = await reset_vector_store(docs, existing_vector_store_id=vs_id, name=f"Categories: {product.product_name}")
            updates["set__product_categories_vs_id"] = res.get("vector_store_id")
        elif vs_id:
            try:
                await client.vector_stores.delete(vs_id)
            except Exception:
                pass
            updates["set__product_categories_vs_id"] = None
    except Exception:
        pass

    try:
        docs = product.product_usage_docs or []
        vs_id = product.product_usage_docs_vs_id
        if docs:
            res = await reset_vector_store(docs, existing_vector_store_id=vs_id, name=f"Usage Docs: {product.product_name}")
            updates["set__product_usage_docs_vs_id"] = res.get("vector_store_id")
        elif vs_id:
            try:
                await client.vector_stores.delete(vs_id)
            except Exception:
                pass
            updates["set__product_usage_docs_vs_id"] = None
    except Exception:
        pass

    if updates:
        try:
            Product.objects(id=product.id).update(**updates)
        except Exception:
            pass


def on_product_post_save(sender, document, **kwargs):
    if isinstance(document, Product):
        _schedule_coro(rebuild_product_vector_stores(document))


signals.post_save.connect(on_product_post_save, sender=Product)
