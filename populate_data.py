#!/usr/bin/env python3

import os
import json
import mongoengine
from dotenv import load_dotenv
from datastore.models import Product, CustomerSegment

# Load environment variables from .env file
load_dotenv()

def connect_to_database():
    mongodb_uri = os.getenv('MONGODB_URI', 'mongodb://localhost:27017/pricing_research')
    print(f"Connecting to MongoDB: {mongodb_uri}")
    mongoengine.connect(host=mongodb_uri)
    print("Successfully connected to MongoDB")

def populate_product_data(json_file_path: str):
    print(f"Loading data from {json_file_path}")
    
    with open(json_file_path, 'r') as f:
        data = json.load(f)
    
    product_data = data.get('product', {})
    pricing_models = data.get('pricing_models', [])
    customer_segments = data.get('customer_segments', [])
    
    print(f"Found {len(pricing_models)} pricing models and {len(customer_segments)} customer segments")
    
    # Create or update product
    product_name = product_data.get('name', 'OpenAI API Platform')
    product = Product.objects(product_name=product_name).first()
    
    if product:
        print(f"Updating existing product: {product_name}")
    else:
        print(f"Creating new product: {product_name}")
        product = Product()
    
    # Map product data
    product.product_name = product_name
    product.product_description = product_data.get('icp_description', '')
    product.product_icp_summary = product_data.get('features_description_summary', '')
    product.product_feature_docs = product_data.get('product_documentations', [])
    
    product.save()
    print(f"Product saved with ID: {product.id}")
    
    # Create customer segments
    segment_count = 0
    for segment_data in customer_segments:
        segment_uid = segment_data.get('customer_segment_uid')
        if not segment_uid:
            continue
            
        segment = CustomerSegment.objects(segment_cdp_uid=segment_uid).first()
        
        if segment:
            print(f"Updating existing segment: {segment_uid}")
        else:
            print(f"Creating new segment: {segment_uid}")
            segment = CustomerSegment()
        
        segment.segment_name = segment_data.get('customer_segment_name', '')
        segment.segment_cdp_uid = segment_uid
        segment.segment_description = segment_data.get('customer_segment_description', '')
        segment.segment_usage_summary = f"Active subscriptions: {segment_data.get('number_of_active_subscriptions', 0)}, Forecast: {segment_data.get('number_of_active_subscriptions_forecast', 0)}"
        
        pricing_model_ids = segment_data.get('pricing_model_ids', [])
        if pricing_model_ids:
            segment.segment_revenue_attribution_summary = f"Associated pricing models: {', '.join(pricing_model_ids)}"
        
        segment.save()
        segment_count += 1
    
    print(f"Successfully populated {segment_count} customer segments")
    return product

def main():
    try:
        connect_to_database()
        
        json_file_path = os.path.join(os.path.dirname(__file__), 'product_data.json')
        if not os.path.exists(json_file_path):
            print(f"Error: {json_file_path} not found")
            return
        
        product = populate_product_data(json_file_path)
        
        print("\n" + "="*50)
        print("DATA POPULATION COMPLETED SUCCESSFULLY")
        print("="*50)
        print(f"Product ID: {product.id}")
        print(f"Product Name: {product.product_name}")
        print(f"Total Customer Segments: {CustomerSegment.objects.count()}")
        print("\nYou can now run experiments using:")
        print(f"python run_experiment.py --product-id {product.id} --objective 'Test pricing strategy' --usecase 'API pricing optimization'")
        
    except Exception as e:
        print(f"Error populating data: {str(e)}")
        raise

if __name__ == "__main__":
    main()
