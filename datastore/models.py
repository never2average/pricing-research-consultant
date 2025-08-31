from mongoengine import Document, EmbeddedDocument, StringField, FloatField, IntField, ListField, URLField, ReferenceField, DateTimeField, DictField, EmbeddedDocumentListField
from datetime import datetime
import os
import tempfile
import requests
from utils.openai_client import openai_client

class Product(Document):
    name = StringField()
    icp_description = StringField()
    unit_level_cogs = StringField()
    features_description_summary = StringField()
    product_documentations = ListField(URLField())
    vector_store_id = StringField()
    
    def save(self, *args, **kwargs):
        # Check if this is a new document or if product_documentations changed
        is_new = self.id is None
        original_docs = []
        
        if not is_new:
            try:
                original_product = Product.objects.get(id=self.id)
                original_docs = original_product.product_documentations
            except Product.DoesNotExist:
                pass
        
        # Save the document first
        super().save(*args, **kwargs)
        
        # Check if we need to create vector store
        should_create_vector_store = False
        
        if is_new and self.product_documentations:
            should_create_vector_store = True
        elif not is_new and self.product_documentations:
            if set(self.product_documentations) != set(original_docs):
                should_create_vector_store = True
        
        if should_create_vector_store:
            try:
                self.create_vector_store_for_product()
            except Exception as e:
                print(f"Error creating vector store for product {self.name}: {e}")
    
    def download_documentation_files(self):
        downloaded_files = []
        
        for url in self.product_documentations:
            try:
                response = requests.get(url)
                response.raise_for_status()
                
                filename = url.split('/')[-1]
                if not filename or '.' not in filename:
                    filename = f"document_{len(downloaded_files)}.txt"
                
                temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=f"_{filename}")
                temp_file.write(response.content)
                temp_file.close()
                
                downloaded_files.append(temp_file.name)
                
            except Exception as e:
                print(f"Error downloading file from {url}: {e}")
                continue
        
        return downloaded_files
    
    def create_vector_store_for_product(self):
        if not self.product_documentations:
            return None
        
        
        downloaded_files = self.download_documentation_files()
        
        if not downloaded_files:
            return None
        
        try:
            file_ids = []
            
            for file_path in downloaded_files:
                with open(file_path, 'rb') as file:
                    uploaded_file = openai_client.files.create(
                        file=file,
                        purpose="assistants"
                    )
                    file_ids.append(uploaded_file.id)
            
            vector_store_name = f"{self.name}_documentation_store"
            metadata = {
                "product_id": str(self.id),
                "product_name": self.name,
                "created_by": "auto_update_hook"
            }
            deleted_vector_store = openai_client.vector_stores.delete(
                vector_store_id=self.vector_store_id
            )
            print(deleted_vector_store)
            
            vector_store = openai_client.vector_stores.create(
                name=vector_store_name,
                file_ids=file_ids,
                metadata=metadata
            )
            
            self.vector_store_id = vector_store.id
            self.save()
            
            return vector_store.id
            
        except Exception as e:
            print(f"Error creating vector store: {e}")
            return None
            
        finally:
            for file_path in downloaded_files:
                try:
                    os.unlink(file_path)
                except:
                    pass

class ProductPricingModel(Document):
    plan_name = StringField()
    unit_price = FloatField()
    min_unit_count = IntField()
    unit_calculation_logic = StringField()
    min_unit_utilization_period = StringField()

class ProductPricingMapping(Document):
    product = ReferenceField(Product)
    pricing_model = ReferenceField(ProductPricingModel)
    is_active = StringField(default="true")
    created_at = DateTimeField(default=datetime.utcnow)

class PricingModelAIGapDiagnosis(Document):
    pricing_model = ReferenceField(ProductPricingModel)
    ai_gap_diagnosis_summary = StringField()
    ai_gap_diagnosis_reasoning = StringField()

class TimeseriesData(EmbeddedDocument):
    date = DateTimeField()
    value = FloatField()

class CustomerSegment(Document):
    product = ReferenceField(Product)
    customer_segment_uid = StringField()
    customer_segment_name = StringField()
    customer_segment_description = StringField()

class PricingPlanSegmentContribution(Document):
    product = ReferenceField(Product)
    customer_segment = ReferenceField(CustomerSegment)
    pricing_plan = ReferenceField(ProductPricingModel)
    revenue_ts_data = EmbeddedDocumentListField(TimeseriesData)
    active_subscriptions = EmbeddedDocumentListField(TimeseriesData)
    revenue_forecast_ts_data = EmbeddedDocumentListField(TimeseriesData)
    active_subscriptions_forecast = EmbeddedDocumentListField(TimeseriesData)

class CustomerUsageAnalysis(Document):
    product = ReferenceField(Product)
    customer_segment = ReferenceField(CustomerSegment)
    customer_uid = StringField()
    customer_task_to_agent = StringField()
    predicted_customer_satisfaction_response = FloatField()
    predicted_customer_satisfaction_response_reasoning = StringField()
    
class RecommendedPricingModel(Document):
    product = ReferenceField(Product)
    customer_segment = ReferenceField(CustomerSegment)
    pricing_plan = ReferenceField(ProductPricingModel)
    new_revenue_forecast_ts_data = EmbeddedDocumentListField(TimeseriesData)

class OrchestrationResult(Document):
    invocation_id = StringField(required=True)
    step_name = StringField(required=True)
    step_order = IntField(required=True)
    product_id = StringField()
    step_input = DictField()
    step_output = DictField()
    created_at = DateTimeField(default=datetime.utcnow)

    meta = {
        'indexes': [
            'invocation_id',
            ('invocation_id', 'step_order'),
        ]
    }