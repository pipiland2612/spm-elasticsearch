import json
import helper
from typing import List, Dict
from datetime import datetime, timezone

# How to use:
# spm_data.json --> data from Jaeger SPM API endpoint
# es_data.json --> data from ES query

def extract_gauge_values_from_file(filepath: str) -> dict[int, float]:
    import json

    with open(filepath, "r", encoding="utf-8") as file:
        data = json.load(file)

    result = {}
    for metric in data.get("metrics", []):
        for point in metric.get("metricPoints", []):
            value = point.get("gaugeValue", {}).get("doubleValue")
            timestamp = point.get("timestamp")
            import math

            if value is not None and timestamp is not None:
                try:
                    num = float(value)
                    if not math.isnan(num):
                        key = helper.timestamp_to_key(timestamp)
                        result[key] = round(num)
                except ValueError:
                    pass
    return result

def extract_percentiles(json_path, percentile):
    import json
    with open(json_path, 'r') as file:
        data = json.load(file)

    # Convert float percentile (e.g., 0.5) to string key (e.g., "50.0")
    percentile_key = f"{percentile * 100:.1f}"

    result = {}
    buckets = data.get("aggregations", {}).get("minute_buckets", {}).get("buckets", [])

    for bucket in buckets:
        key = bucket.get("key")
        value_ms = bucket.get("percentiles_of_bucket_of_10m_window", {}).get("values", {}).get(percentile_key)

        if value_ms is not None:
            result[key] = value_ms / 1000

    return result

# Example usage:
arr1 = extract_gauge_values_from_file("./json/spm_getLatencies.json")
arr2 = extract_percentiles("./json/es_getLatencies.json", 0.95)
helper.plot_two_maps(arr1, arr2, "GetLatencies")
