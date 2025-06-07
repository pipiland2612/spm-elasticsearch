import json
import sys
from statistics import mean

def compute_mean_rates(pathToJsonFile):
    with open(pathToJsonFile, 'r') as f:
        data = json.load(f)

    operations = data.get("aggregations", {}).get("operations", {}).get("buckets", [])
    result = {}

    for operation in operations:
        op_name = operation.get("key")
        rate_buckets = operation.get("requests_per_bucket", {}).get("buckets", [])

        # Extract all non-null rate_per_second values
        rates = [
            bucket["rate_per_second"]["value"]
            for bucket in rate_buckets
            if "rate_per_second" in bucket and bucket["rate_per_second"]["value"] is not None
        ]

        if rates:
            result[op_name] = mean(rates)
        else:
            result[op_name] = 0.0  # or None if you prefer

    return result
import os

mean_rates = compute_mean_rates("./json/mean_data.json")
print(json.dumps(mean_rates, indent=2))