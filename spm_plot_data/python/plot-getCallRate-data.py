import matplotlib.pyplot as plt
import json
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


def plot_two_maps(map1: dict, map2: dict, label1="SPM API", label2="ES query"):
    # Sort items by keys for both maps
    sorted_items1 = sorted(map1.items())
    sorted_items2 = sorted(map2.items())

    # Convert keys (assumed to be timestamp in ms) to datetime objects for x-axis
    x1 = [datetime.fromtimestamp(k / 1000) for k, v in sorted_items1]
    y1 = [v for k, v in sorted_items1]

    x2 = [datetime.fromtimestamp(k / 1000) for k, v in sorted_items2]
    y2 = [v for k, v in sorted_items2]

    plt.figure(figsize=(12, 6))
    plt.plot(x1, y1, marker='o', label=label1)
    plt.plot(x2, y2, marker='x', label=label2)

    plt.xlabel('Time')
    plt.ylabel('Value')
    plt.title('GetCallRate (req/s)')
    plt.legend()
    plt.grid(True)
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.show()

# Example usage:
arr1 = extract_gauge_values_from_file("./json/spm_data.json")
print(len(arr1))
arr2 = extract_call_rate_per_second_from_file("./json/es_data.json")
print(len(arr2))
plot_two_maps(arr1, arr2)
