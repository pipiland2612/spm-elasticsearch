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

    for bucket in buckets:
        call_rate = bucket.get("rate_per_second", {}).get("value", 0.0)

        key = bucket.get("key")  # the timestamp key, e.g., 1747678380000
        if key is not None:
            result[key] = call_rate

    return result

def divide_common_keys(dict1: dict[int, float], dict2: dict[int, float]) -> dict[int, float]:
    result = {}
    for key in dict1.keys() & dict2.keys():  # intersection of keys
        if dict2[key] != 0:  # avoid division by zero
            result[key] = dict1[key] / dict2[key]
        else:
            result[key] = 0
    return result



# Example usage:
arr1 = extract_call_rate_per_second_from_file("./json/es_getCallRate.json")
arr2 = extract_call_rate_per_second_from_file("./json/es_getErrorRate.json")
arr3 = divide_common_keys(arr1, arr2)
# helper.plot_two_maps(arr1, arr2)
helper.plot_single_map(arr3, "Error Rate")