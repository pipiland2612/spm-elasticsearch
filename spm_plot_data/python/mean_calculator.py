import json
import sys
from statistics import mean

def compute_mean_rates_callRate(pathToJsonFile):
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


def extract_95th_percentile_means(path_to_file):
    with open(path_to_file, "r") as f:
        data = json.load(f)

    result = {}

    buckets = data.get("aggregations", {}).get("operations", {}).get("buckets", [])
    for operation in buckets:
        op_name = operation.get("key")
        ten_min_buckets = operation.get("minute_buckets", {}).get("buckets", [])

        # Extract all valid 95.0 percentile values from 10m windows
        values_95 = [
            b["percentiles_of_bucket_of_10m_window"]["values"].get("95.0")
            for b in ten_min_buckets
            if "percentiles_of_bucket_of_10m_window" in b and
               "values" in b["percentiles_of_bucket_of_10m_window"] and
               "95.0" in b["percentiles_of_bucket_of_10m_window"]["values"]
        ]

        if values_95:
            result[op_name] = mean(values_95) / 1000

    return result

mean_rates = compute_mean_rates_callRate("./json/mean_getCallRate.json")
mean_percentiles = extract_95th_percentile_means("./json/mean_getLatencies.json")
print("GetCallRate")
print(json.dumps(mean_rates, indent=2))
print("GetLatencies")
print(json.dumps(mean_percentiles, indent=2))