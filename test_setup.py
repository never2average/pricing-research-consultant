#!/usr/bin/env python3

import os
import json
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def test_product_data_structure():
    print("Testing product_data.json structure...")
    
    json_file_path = os.path.join(os.path.dirname(__file__), 'product_data.json')
    if not os.path.exists(json_file_path):
        print("❌ product_data.json not found")
        return False
    
    try:
        with open(json_file_path, 'r') as f:
            data = json.load(f)
        
        # Check required structure
        required_keys = ['product', 'pricing_models', 'customer_segments']
        for key in required_keys:
            if key not in data:
                print(f"❌ Missing key: {key}")
                return False
        
        product = data['product']
        pricing_models = data['pricing_models']
        customer_segments = data['customer_segments']
        
        print(f"✅ Product: {product.get('name', 'Unknown')}")
        print(f"✅ Pricing models: {len(pricing_models)}")
        print(f"✅ Customer segments: {len(customer_segments)}")
        
        # Validate segments have required fields
        for i, segment in enumerate(customer_segments):
            if 'customer_segment_uid' not in segment:
                print(f"❌ Segment {i} missing customer_segment_uid")
                return False
        
        print("✅ product_data.json structure is valid")
        return True
        
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON: {str(e)}")
        return False
    except Exception as e:
        print(f"❌ Error reading file: {str(e)}")
        return False

def test_imports():
    print("\nTesting Python imports...")
    
    try:
        import mongoengine
        print("✅ mongoengine imported successfully")
    except ImportError as e:
        print(f"❌ mongoengine import failed: {str(e)}")
        return False
    
    try:
        from datastore.models import Product, CustomerSegment, PricingExperimentRequest
        print("✅ datastore.models imported successfully")
    except ImportError as e:
        print(f"❌ datastore.models import failed: {str(e)}")
        return False
    
    try:
        from logical_functions.workflow_manager import start_experiment_workflow
        print("✅ workflow_manager imported successfully")
    except ImportError as e:
        print(f"❌ workflow_manager import failed: {str(e)}")
        return False
    
    return True

def test_environment():
    print("\nTesting environment variables...")
    
    openai_key = os.getenv('OPENAI_API_KEY')
    if openai_key:
        print("✅ OPENAI_API_KEY is set")
        if len(openai_key) > 20:
            print(f"   Key preview: {openai_key[:8]}...{openai_key[-4:]}")
        else:
            print("   Key appears to be short - please verify")
    else:
        print("⚠️  OPENAI_API_KEY not set - required for running experiments")
    
    mongodb_uri = os.getenv('MONGODB_URI', 'mongodb://localhost:27017/pricing_research')
    print(f"✅ MongoDB URI: {mongodb_uri}")
    
    return True

def main():
    print("🧪 TESTING SETUP FOR PRICING RESEARCH CONSULTANT")
    print("=" * 60)
    
    all_tests_passed = True
    
    # Test 1: Product data structure
    if not test_product_data_structure():
        all_tests_passed = False
    
    # Test 2: Python imports
    if not test_imports():
        all_tests_passed = False
    
    # Test 3: Environment
    test_environment()
    
    print("\n" + "=" * 60)
    if all_tests_passed:
        print("🎉 ALL TESTS PASSED!")
        print("\nYou can now run:")
        print("1. python3 setup_and_run.py    # Complete setup and run")
        print("2. python3 populate_data.py    # Just populate database")
        print("3. python3 run_experiment.py   # Run experiments manually")
    else:
        print("❌ SOME TESTS FAILED")
        print("\nPlease fix the issues above before proceeding.")
    
    return all_tests_passed

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
