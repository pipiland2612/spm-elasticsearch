import json
import helper
from typing import List, Dict
from datetime import datetime, timezone

# How to use:
# spm_data.json --> data from Jaeger SPM API endpoint 
# es_data.json --> data from ES query



def timestamp_to_key(timestamp_str: str) -> int:
    dt = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
    return int(dt.timestamp() * 1000)

def extract_gauge_values_from_file(filepath: str) -> dict[int, float]:
    import json

    with open(filepath, "r", encoding="utf-8") as file:
        data = json.load(file)

    result = {}
    for metric in data.get("metrics", []):
        for point in metric.get("metricPoints", []):
            value = point.get("gaugeValue", {}).get("doubleValue")
            timestamp = point.get("timestamp")
            if value is not None and timestamp is not None:
                key = timestamp_to_key(timestamp)
                result[key] = value

    return result

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
arr1 = extract_gauge_values_from_file("./json/spm_getCallRate.json")
print(len(arr1))
arr2 = extract_call_rate_per_second_from_file("./json/es_getCallRate.json")
print(len(arr2))
helper.plot_two_maps(arr1, arr2)
