#!/usr/bin/env python3

import os
import sys
import argparse
import mongoengine
from datetime import datetime, timezone
from dotenv import load_dotenv
from datastore.models import PricingExperimentRequest, Product, PricingExperimentRuns
from logical_functions.workflow_manager import start_experiment_workflow

# Load environment variables from .env file
load_dotenv()

def connect_to_database():
    mongodb_uri = os.getenv('MONGODB_URI', 'mongodb://localhost:27017/pricing_research')
    print(f"Connecting to MongoDB: {mongodb_uri}")
    mongoengine.connect(host=mongodb_uri)
    print("Successfully connected to MongoDB")

def list_products():
    products = Product.objects()
    if not products:
        print("No products found in database. Run populate_data.py first.")
        return
    
    print("\nAvailable Products:")
    print("-" * 50)
    for product in products:
        print(f"ID: {product.id}")
        print(f"Name: {product.product_name}")
        print(f"Description: {product.product_description[:100]}...")
        print("-" * 50)

def list_experiments():
    experiments = PricingExperimentRequest.objects().order_by('-experiment_number')
    if not experiments:
        print("No experiments found.")
        return
    
    print("\nExisting Experiments:")
    print("-" * 80)
    for exp in experiments:
        print(f"Experiment #{exp.experiment_number}")
        print(f"Product: {exp.product.product_name if exp.product else 'Unknown'}")
        print(f"Objective: {exp.objective}")
        print(f"Use Case: {exp.usecase}")
        print(f"Stage: {exp.experiment_gen_stage}")
        print(f"Created: {exp.created_on}")
        
        runs = PricingExperimentRuns.objects(experiment_request=exp).count()
        print(f"Runs: {runs}")
        print("-" * 80)

def create_and_run_experiment(product_id: str, objective: str, usecase: str):
    try:
        product = Product.objects(id=product_id).first()
        if not product:
            print(f"Error: Product with ID {product_id} not found")
            list_products()
            return
        
        # Get next experiment number
        last_experiment = PricingExperimentRequest.objects().order_by('-experiment_number').first()
        next_experiment_number = (last_experiment.experiment_number + 1) if last_experiment else 1
        
        print(f"Creating experiment #{next_experiment_number} for product: {product.product_name}")
        
        # Create experiment request
        experiment_request = PricingExperimentRequest(
            product=product,
            experiment_number=next_experiment_number,
            objective=objective,
            usecase=usecase,
            experiment_gen_stage="product_context_initialized",
            created_on=datetime.now(timezone.utc)
        )
        experiment_request.save()
        
        print(f"Experiment created with ID: {experiment_request.id}")
        print(f"Starting workflow for experiment #{next_experiment_number}...")
        print("This may take several minutes as it processes through multiple AI agents...")
        
        # Start the workflow
        start_experiment_workflow(experiment_request)
        
        print(f"\nExperiment #{next_experiment_number} completed successfully!")
        
        # Show final results
        experiment_request.reload()
        final_run = PricingExperimentRuns.objects(experiment_request=experiment_request).order_by('-created_on').first()
        
        if final_run:
            print("\nFinal Results:")
            print("=" * 50)
            print(f"Final Stage: {final_run.experiment_gen_stage}")
            if final_run.experimental_pricing_plan:
                print(f"Pricing Plan: {final_run.experimental_pricing_plan[:200]}...")
            if final_run.cashflow_feasibility_comments:
                print(f"Cashflow Comments: {final_run.cashflow_feasibility_comments[:200]}...")
            if final_run.cashflow_no_negative_impact_approval_given:
                print("✅ Cashflow approved for deployment")
            else:
                print("⚠️  Cashflow approval pending")
        
    except Exception as e:
        print(f"Error running experiment: {str(e)}")
        raise

def main():
    parser = argparse.ArgumentParser(description='Run pricing research experiments')
    parser.add_argument('--product-id', help='Product ID to run experiment for')
    parser.add_argument('--objective', help='Experiment objective', 
                       default='Optimize pricing strategy based on market analysis')
    parser.add_argument('--usecase', help='Experiment use case',
                       default='API pricing model optimization')
    parser.add_argument('--list-products', action='store_true', help='List available products')
    parser.add_argument('--list-experiments', action='store_true', help='List existing experiments')
    
    args = parser.parse_args()
    
    try:
        connect_to_database()
        
        if args.list_products:
            list_products()
            return
            
        if args.list_experiments:
            list_experiments()
            return
        
        if not args.product_id:
            print("Error: --product-id is required")
            print("\nUse --list-products to see available products")
            list_products()
            return
        
        # Check if required environment variables are set
        required_env_vars = ['OPENAI_API_KEY']
        missing_vars = [var for var in required_env_vars if not os.getenv(var)]
        if missing_vars:
            print(f"Error: Missing required environment variables: {', '.join(missing_vars)}")
            print("\nPlease set the following environment variables:")
            for var in missing_vars:
                print(f"export {var}='your-key-here'")
            return
        
        create_and_run_experiment(args.product_id, args.objective, args.usecase)
        
    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
