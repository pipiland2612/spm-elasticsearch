import json
import helper
from typing import List, Dict
from datetime import datetime, timezone

# How to use:
# spm_data.json --> data from Jaeger SPM API endpoint 
# es_data.json --> data from ES query


def extract_call_rate_per_second_from_file(filepath: str) -> dict[int, float]:
    import json

    with open(filepath, "r", encoding="utf-8") as file:
        data = json.load(file)

    buckets = data.get("aggregations", {}).get("requests_per_bucket", {}).get("buckets", [])
    result = {}

    empty_value= 0.0  # Default value for empty buckets
    for bucket in buckets:
        call_rate = bucket.get("rate_per_second", {}).get("value", 0.0)
        
        key = bucket.get("key")  # the timestamp key, e.g., 1747678380000
        if key is not None:
            result[key] = call_rate
        
        if call_rate is None:
            empty_value+= 1.0  # Increment empty value for each empty bucket        
    
    print(f"Empty buckets: {empty_value}")
    
    return result

# Example usage:
arr1 = helper.extract_gauge_values_from_file("./json/spm_getCallRate.json")
print(len(arr1))
arr2 = extract_call_rate_per_second_from_file("./json/es_getCallRate.json")
print(len(arr2))
helper.plot_two_maps(arr1, arr2, "GetCallRate")
