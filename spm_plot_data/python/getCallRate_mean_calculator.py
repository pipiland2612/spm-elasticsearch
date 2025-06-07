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


import json

def compute_mean_rate_single_bucket_file(pathToJsonFile):
    with open(pathToJsonFile, 'r') as f:
        data = json.load(f)

    buckets = data.get("aggregations", {}).get("requests_per_bucket", {}).get("buckets", [])

    # Extract all available rate_per_second values
    rate_values = [
        bucket["rate_per_second"]["value"]
        for bucket in buckets
        if "rate_per_second" in bucket and bucket["rate_per_second"]["value"] is not None
    ]

    if not rate_values:
        return 0.0  # Avoid division by zero

    return mean(rate_values)

mean_rates = compute_mean_rates("./json/mean_getCallRate.json")
print(json.dumps(mean_rates, indent=2))