import os
import sys
import json
import argparse
from orchestrator import final_agent
from datastore.connectors import (
    connect_db,
    create_from_json_file,
    delete_one,
    delete_many,
    get_one,
    list_all_ids,
    list_one_markdown,
    list_all_markdown,
)
from dotenv import load_dotenv

load_dotenv()
connect_db()


def process_json_file(path):
    return create_from_json_file(path)

 


def print_creation_results(product, pricing_models, segments):
    """Print beautified creation results"""
    print("\n" + "="*60)
    print("🎉 CREATION SUCCESSFUL")
    print("="*60)

    print(f"\n📦 Product Created:")
    print(f"   ID: {product.id}")
    print(f"   Name: {product.name}")

    print(f"\n💰 Pricing Models Created:")
    if isinstance(pricing_models, list):
        for i, model in enumerate(pricing_models, 1):
            print(f"   {i}. ID: {model.id}")
            print(f"      Plan: {model.plan_name}")
            print(f"      Price: ${model.unit_price}")
    else:
        print(f"   ID: {pricing_models.id}")
        print(f"   Plan: {pricing_models.plan_name}")
        print(f"   Price: ${pricing_models.unit_price}")

    print(f"\n👥 Customer Segments Created:")
    for i, segment in enumerate(segments, 1):
        print(f"   {i}. ID: {segment.id}")
        print(f"      Name: {segment.customer_segment_name}")
        print(f"      UID: {segment.customer_segment_uid}")

    print("\n" + "="*60)
    print(f"✅ Total: 1 Product, {len(pricing_models) if isinstance(pricing_models, list) else 1} Pricing Model(s), {len(segments)} Segment(s)")
    print("="*60 + "\n")


def build_parser():
    description = """
Pricing Research Consultant CLI Tool

A comprehensive tool for managing products, pricing models, and customer segments,
with advanced pricing analysis and recommendation capabilities.

Examples:
  # Create from JSON file
  python main.py --create --json product_data.json
  
  
  
  # Run pricing analysis
  python main.py --orchestrator --product-id PROD123 --use-case "SaaS optimization"
  
  # List all products
  python main.py --listall products
  
  # View specific pricing model
  python main.py --list pricing_models MODEL456
  
  # Delete a customer segment
  python main.py --delete customer_segments SEG789
    """
    
    parser = argparse.ArgumentParser(
        prog="pricing-cli",
        description=description,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    # Main operation modes
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument(
        "--create", 
        action="store_true",
        help="Create new products, pricing models, and segments from input data"
    )
    mode.add_argument(
        "--orchestrator", 
        action="store_true",
        help="Run comprehensive pricing analysis and generate recommendations"
    )
    mode.add_argument(
        "--delete", 
        nargs=2, 
        metavar=("collection", "id"),
        help="Delete a single document from specified collection (products, pricing_models, customer_segments)"
    )
    mode.add_argument(
        "--deletemany", 
        nargs=2, 
        metavar=("collection", "ids"),
        help="Delete multiple documents from collection (comma-separated IDs)"
    )
    mode.add_argument(
        "--list", 
        dest="list_one", 
        nargs=2, 
        metavar=("collection", "id"),
        help="Display detailed information about a specific document"
    )
    mode.add_argument(
        "--listall", 
        nargs=1, 
        metavar=("collection",),
        help="List all documents in the specified collection"
    )

    # Input/Output options
    io_group = parser.add_mutually_exclusive_group(required=False)
    io_group.add_argument(
        "--json", 
        dest="input_json",
        metavar="FILE",
        help="Input JSON file path (required with --create)"
    )
    

    # Additional parameters
    parser.add_argument(
        "--product-id",
        metavar="ID",
        help="Product ID for orchestrator analysis (required with --orchestrator)"
    )
    parser.add_argument(
        "--use-case",
        metavar="DESCRIPTION",
        help="Optional use case description for targeted analysis"
    )
    parser.add_argument(
        "--pricing-objective",
        metavar="OBJECTIVE",
        help="Optional pricing objective to guide the analysis (e.g., 'maximize revenue', 'increase market share', 'optimize for retention')"
    )
    
    return parser




parser = build_parser()
args = parser.parse_args()

if args.create:
    if not args.input_json:
        parser.error("--json is required with --create")

    product, pricing_models, segments = process_json_file(args.input_json)

    print_creation_results(product, pricing_models, segments)

elif args.orchestrator:
    if not args.product_id:
        parser.error("--product-id is required with --orchestrator")
    try:
        final_agent(str(args.product_id), args.use_case, None, args.pricing_objective)
        print("Orchestrator run complete")
    except Exception as e:
        print(f"Error running orchestrator.final_agent: {e}")
elif args.delete:
    collection, doc_id = args.delete
    try:
        delete_one(collection, doc_id)
        print(f"Deleted {collection}: {doc_id}")
    except Exception as e:
        print(f"Error deleting {collection} {doc_id}: {e}")
        sys.exit(1)
elif args.deletemany:
    collection, ids_csv = args.deletemany
    ids = [x.strip() for x in ids_csv.split(",") if x.strip()]
    result = delete_many(collection, ids)
    print(f"Deleted {result['deleted']}/{result['requested']} from {collection}")
    if result["errors"]:
        print(f"Failed ids: {result['errors']}")
elif args.list_one:
    collection, doc_id = args.list_one
    try:
        print(list_one_markdown(collection, doc_id))
    except Exception as e:
        print(f"Error fetching {collection} {doc_id}: {e}")
        sys.exit(1)
elif args.listall:
    collection = args.listall[0]
    try:
        print(list_all_markdown(collection))
    except Exception as e:
        print(f"Error listing {collection}: {e}")
        sys.exit(1)