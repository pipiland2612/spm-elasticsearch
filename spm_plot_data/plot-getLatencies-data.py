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
            import math

            if value is not None and timestamp is not None:
                try:
                    num = float(value)
                    if not math.isnan(num):
                        key = timestamp_to_key(timestamp)
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
    plt.title('GetLatencies 95th percentile')
    plt.legend()
    plt.grid(True)
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.show()

# Example usage:
arr1 = extract_gauge_values_from_file("spm_data.json")
arr2 = extract_percentiles("./percentiles_spm_data.json", 0.95)
plot_two_maps(arr1, arr2)
