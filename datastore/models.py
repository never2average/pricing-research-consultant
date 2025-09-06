from datetime import datetime
import os
import tempfile
import requests
from utils.openai_client import openai_client
from mongoengine import ReferenceField, DateTimeField, DynamicField, EmbeddedDocumentListField
from mongoengine import Document, EmbeddedDocument, StringField, FloatField, IntField, ListField, URLField

class Competitors(EmbeddedDocument):
    competitor_name = StringField()
    website_url = StringField()
    product_description = StringField()

class Product(Document):
    name = StringField()
    category = StringField()
    icp_description = StringField()
    unit_level_cogs = StringField()
    features_description_summary = StringField()
    competitors = EmbeddedDocumentListField(Competitors)
    product_documentations = ListField(URLField())
    marketing_documentations = ListField(URLField())
    vector_store_id = StringField()
    marketing_vector_store_id = StringField()
    
    def save(self, *args, **kwargs):
        # Validate doc_urls for new products
        if self.id is None and self.product_documentations:
            self._validate_and_clean_doc_urls()
        if self.id is None and self.marketing_documentations:
            self._validate_and_clean_marketing_doc_urls()

        # Check if this is a new document or if documentations changed
        is_new = self.id is None
        original_docs = []
        original_marketing_docs = []

        if not is_new:
            try:
                original_product = Product.objects.get(id=self.id)
                original_docs = original_product.product_documentations
                original_marketing_docs = original_product.marketing_documentations
            except Product.DoesNotExist:
                pass

        # Save the document first
        super().save(*args, **kwargs)

        # Check if we need to create product vector store
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

        # Check if we need to create marketing vector store
        should_create_marketing_vector_store = False

        if is_new and self.marketing_documentations:
            should_create_marketing_vector_store = True
        elif not is_new and self.marketing_documentations:
            if set(self.marketing_documentations) != set(original_marketing_docs):
                should_create_marketing_vector_store = True

        if should_create_marketing_vector_store:
            try:
                self.create_marketing_vector_store()
            except Exception as e:
                print(f"Error creating marketing vector store for product {self.name}: {e}")

    def _validate_and_clean_doc_urls(self):
        """Validate and clean documentation URLs for new products"""
        if not self.product_documentations:
            return

        from urllib.parse import urlparse
        import re

        cleaned_urls = []
        for url in self.product_documentations:
            if not isinstance(url, str):
                print(f"Warning: Invalid doc URL type {type(url)}, skipping: {url}")
                continue

            url = url.strip()
            if not url:
                continue

            # Basic URL validation
            try:
                parsed = urlparse(url)
                if not parsed.scheme or not parsed.netloc:
                    # Try to add https:// if missing scheme
                    if not parsed.scheme and parsed.path:
                        url = f"https://{url}"
                        parsed = urlparse(url)
                        if not parsed.scheme or not parsed.netloc:
                            print(f"Warning: Invalid URL format, skipping: {url}")
                            continue
                    else:
                        print(f"Warning: Invalid URL format, skipping: {url}")
                        continue

                # Additional validation - check for common file extensions or documentation patterns
                path = parsed.path.lower()
                if not any(ext in path for ext in ['.pdf', '.doc', '.docx', '.txt', '.md', '.html', '.htm', '/docs', '/documentation', '/help']):
                    print(f"Warning: URL doesn't appear to be documentation, but adding anyway: {url}")

                cleaned_urls.append(url)

            except Exception as e:
                print(f"Warning: Error validating URL {url}: {e}")
                continue

        self.product_documentations = cleaned_urls
        if cleaned_urls:
            print(f"Validated {len(cleaned_urls)} documentation URLs for new product")
        else:
            print("Warning: No valid documentation URLs found for new product")

    def _validate_and_clean_marketing_doc_urls(self):
        """Validate and clean marketing documentation URLs for new products"""
        if not self.marketing_documentations:
            return

        from urllib.parse import urlparse
        import re

        cleaned_urls = []
        for url in self.marketing_documentations:
            if not isinstance(url, str):
                print(f"Warning: Invalid marketing doc URL type {type(url)}, skipping: {url}")
                continue

            url = url.strip()
            if not url:
                continue

            # Basic URL validation
            try:
                parsed = urlparse(url)
                if not parsed.scheme or not parsed.netloc:
                    # Try to add https:// if missing scheme
                    if not parsed.scheme and parsed.path:
                        url = f"https://{url}"
                        parsed = urlparse(url)
                        if not parsed.scheme or not parsed.netloc:
                            print(f"Warning: Invalid marketing URL format, skipping: {url}")
                            continue
                    else:
                        print(f"Warning: Invalid marketing URL format, skipping: {url}")
                        continue

                # Additional validation for marketing materials - broader patterns
                path = parsed.path.lower()
                if not any(ext in path for ext in ['.pdf', '.doc', '.docx', '.txt', '.md', '.html', '.htm', '/docs', '/documentation', '/help', '/marketing', '/brand', '/assets', '/media']):
                    print(f"Warning: URL doesn't appear to be marketing documentation, but adding anyway: {url}")

                cleaned_urls.append(url)

            except Exception as e:
                print(f"Warning: Error validating marketing URL {url}: {e}")
                continue

        self.marketing_documentations = cleaned_urls
        if cleaned_urls:
            print(f"Validated {len(cleaned_urls)} marketing documentation URLs for new product")
        else:
            print("Warning: No valid marketing documentation URLs found for new product")

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

    def download_marketing_documentation_files(self):
        downloaded_files = []
        
        for url in self.marketing_documentations:
            try:
                response = requests.get(url)
                response.raise_for_status()
                
                filename = url.split('/')[-1]
                if not filename or '.' not in filename:
                    filename = f"marketing_document_{len(downloaded_files)}.txt"
                
                temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=f"_{filename}")
                temp_file.write(response.content)
                temp_file.close()
                
                downloaded_files.append(temp_file.name)
                
            except Exception as e:
                print(f"Error downloading marketing file from {url}: {e}")
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

            # Only delete existing vector store if this is not a new product
            if self.vector_store_id:
                try:
                    deleted_vector_store = openai_client.vector_stores.delete(
                        vector_store_id=self.vector_store_id
                    )
                    print(f"Deleted existing vector store: {deleted_vector_store}")
                except Exception as e:
                    print(f"Error deleting existing vector store: {e}")

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

    def create_marketing_vector_store(self):
        if not self.marketing_documentations:
            return None

        downloaded_files = self.download_marketing_documentation_files()

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

            vector_store_name = f"{self.name}_marketing_store"
            metadata = {
                "product_id": str(self.id),
                "product_name": self.name,
                "created_by": "auto_update_hook",
                "store_type": "marketing"
            }

            # Only delete existing marketing vector store if this is not a new product
            if self.marketing_vector_store_id:
                try:
                    deleted_vector_store = openai_client.vector_stores.delete(
                        vector_store_id=self.marketing_vector_store_id
                    )
                    print(f"Deleted existing marketing vector store: {deleted_vector_store}")
                except Exception as e:
                    print(f"Error deleting existing marketing vector store: {e}")

            vector_store = openai_client.vector_stores.create(
                name=vector_store_name,
                file_ids=file_ids,
                metadata=metadata
            )

            self.marketing_vector_store_id = vector_store.id
            self.save()

            return vector_store.id

        except Exception as e:
            print(f"Error creating marketing vector store: {e}")
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
    step_input = DynamicField()
    step_output = DynamicField()
    created_at = DateTimeField(default=datetime.utcnow)

    meta = {
        'indexes': [
            'invocation_id',
            ('invocation_id', 'step_order'),
        ]
    }