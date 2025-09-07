#!/usr/bin/env python3

import os
import sys
import subprocess
import json
import mongoengine
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def check_environment():
    print("Checking environment setup...")
    
    # Check Python version
    if sys.version_info < (3, 8):
        print("Error: Python 3.8+ required")
        return False
    
    # Check required environment variables
    required_vars = {
        'OPENAI_API_KEY': 'OpenAI API key for AI agents',
        'MONGODB_URI': 'MongoDB connection string (optional, defaults to localhost)'
    }
    
    missing_vars = []
    for var, description in required_vars.items():
        if not os.getenv(var):
            if var == 'MONGODB_URI':
                print(f"ℹ️  {var} not set, using default: mongodb://localhost:27017/pricing_research")
            else:
                missing_vars.append(f"{var}: {description}")
    
    if missing_vars:
        print("❌ Missing required environment variables:")
        for var in missing_vars:
            print(f"   {var}")
        print("\nPlease set them using:")
        for var in missing_vars:
            var_name = var.split(':')[0]
            print(f"   export {var_name}='your-value-here'")
        return False
    
    print("✅ Environment check passed")
    return True

def check_mongodb_connection():
    print("Testing MongoDB connection...")
    try:
        mongodb_uri = os.getenv('MONGODB_URI', 'mongodb://localhost:27017/pricing_research')
        mongoengine.connect(host=mongodb_uri)
        print("✅ MongoDB connection successful")
        return True
    except Exception as e:
        print(f"❌ MongoDB connection failed: {str(e)}")
        print("\nMongoDB setup options:")
        print("1. Local MongoDB: Install and run 'mongod'")
        print("2. Docker: docker run -d -p 27017:27017 mongo:latest")
        print("3. MongoDB Atlas: Set MONGODB_URI to your Atlas connection string")
        return False

def check_data_file():
    json_file_path = os.path.join(os.path.dirname(__file__), 'product_data.json')
    if not os.path.exists(json_file_path):
        print(f"❌ product_data.json not found at {json_file_path}")
        return False
    
    try:
        with open(json_file_path, 'r') as f:
            data = json.load(f)
        
        if 'product' not in data or 'customer_segments' not in data:
            print("❌ Invalid product_data.json format")
            return False
        
        print("✅ product_data.json found and valid")
        return True
    except Exception as e:
        print(f"❌ Error reading product_data.json: {str(e)}")
        return False

def run_population_script():
    print("\n" + "="*50)
    print("POPULATING DATABASE FROM product_data.json")
    print("="*50)
    
    try:
        result = subprocess.run([sys.executable, 'populate_data.py'], 
                              capture_output=True, text=True, check=True)
        print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Population script failed: {e.stderr}")
        return False

def get_product_id():
    try:
        from datastore.models import Product
        product = Product.objects().first()
        if product:
            return str(product.id)
        else:
            print("❌ No products found in database")
            return None
    except Exception as e:
        print(f"❌ Error getting product ID: {str(e)}")
        return None

def run_experiment(product_id: str):
    print("\n" + "="*50)
    print("RUNNING PRICING EXPERIMENT")
    print("="*50)
    
    try:
        cmd = [
            sys.executable, 'run_experiment.py',
            '--product-id', product_id,
            '--objective', 'Optimize pricing strategy for OpenAI API Platform',
            '--usecase', 'Multi-tier API pricing optimization with usage-based models'
        ]
        
        print(f"Running: {' '.join(cmd)}")
        subprocess.run(cmd, check=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Experiment failed with exit code {e.returncode}")
        return False

def main():
    print("🚀 PRICING RESEARCH CONSULTANT - SETUP AND RUN")
    print("=" * 60)
    
    # Step 1: Environment check
    if not check_environment():
        sys.exit(1)
    
    # Step 2: MongoDB connection check
    if not check_mongodb_connection():
        sys.exit(1)
    
    # Step 3: Data file check
    if not check_data_file():
        sys.exit(1)
    
    # Step 4: Populate database
    if not run_population_script():
        sys.exit(1)
    
    # Step 5: Get product ID
    product_id = get_product_id()
    if not product_id:
        sys.exit(1)
    
    # Step 6: Run experiment
    print(f"\nProduct ID found: {product_id}")
    print("Starting pricing experiment workflow...")
    print("This will run through multiple AI agents and may take 10-15 minutes...")
    
    if run_experiment(product_id):
        print("\n🎉 SUCCESS! Pricing research experiment completed.")
        print("\nNext steps:")
        print("1. Review the experiment results")
        print("2. Run additional experiments with different parameters")
        print("3. Use the FastAPI server for web interface: python main.py")
    else:
        print("\n❌ Experiment failed. Check the logs above for details.")
        sys.exit(1)

if __name__ == "__main__":
    main()
