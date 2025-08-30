import os
import sys
import json
import argparse
from orchestrator import final_agent
from datastore.connectors import (
    connect_db,
    create_from_json_file,
    create_from_csv_file,
    delete_one,
    delete_many,
    get_one,
    list_all_ids,
)


connect_db()


def process_json_file(path):
    return create_from_json_file(path)


def process_csv_file(path):
    return create_from_csv_file(path)


def build_parser():
    parser = argparse.ArgumentParser(prog="pricing-cli")
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--create", action="store_true")
    mode.add_argument("--orchestrator", action="store_true")
    mode.add_argument("--delete", nargs=2, metavar=("collection", "id"))
    mode.add_argument("--deletemany", nargs=2, metavar=("collection", "ids"))
    mode.add_argument("--list", dest="list_one", nargs=2, metavar=("collection", "id"))
    mode.add_argument("--listall", nargs=1, metavar=("collection",))

    io_group = parser.add_mutually_exclusive_group(required=False)
    io_group.add_argument("--json", dest="input_json")
    io_group.add_argument("--csv", dest="input_csv")

    parser.add_argument("--product-id")
    parser.add_argument("--use-case")
    return parser




parser = build_parser()
args = parser.parse_args()

if args.create:
    if not args.input_json and not args.input_csv:
        parser.error("--json or --csv is required with --create")

    if args.input_json:
        product, pricing_model, segments = process_json_file(args.input_json)
    else:
        product, pricing_model, segments = process_csv_file(args.input_csv)

    print("Created:")
    print(f"- Product: {str(product.id)}")
    print(f"- ProductPricingModel: {str(pricing_model.id)}")
    print(f"- CustomerSegments: {[str(s.id) for s in segments]}")

elif args.orchestrator:
    if not args.product_id:
        parser.error("--product-id is required with --orchestrator")
    try:
        final_agent(str(args.product_id), args.use_case, None)
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
        obj = get_one(collection, doc_id)
        try:
            print(obj.to_json())
        except Exception:
            from bson import json_util
            print(json.dumps(obj.to_mongo().to_dict(), default=json_util.default))
    except Exception as e:
        print(f"Error fetching {collection} {doc_id}: {e}")
        sys.exit(1)
elif args.listall:
    collection = args.listall[0]
    try:
        ids = list_all_ids(collection)
        norm = collection
        print(json.dumps({"collection": norm, "ids": ids}))
    except Exception as e:
        print(f"Error listing {collection}: {e}")
        sys.exit(1)