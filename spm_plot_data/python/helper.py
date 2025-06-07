import matplotlib.pyplot as plt
from typing import List, Dict, Optional
from datetime import datetime, timezone
import numpy as np


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

def timestamp_to_key(timestamp_str: str) -> int:
    dt = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
    return int(dt.timestamp() * 1000)

def plot_two_maps(map1: dict, map2: dict, maptitle: str, label1="SPM API", label2="ES query", x_limits: Optional[tuple[int, int]] = None):
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
    plt.title(maptitle)
    plt.legend()
    plt.grid(True)
    plt.xticks(rotation=45)

    # Apply x-axis limits if provided
    if x_limits:
        start_time = datetime.fromtimestamp(x_limits[0] / 1000)
        end_time = datetime.fromtimestamp(x_limits[1] / 1000)
        plt.xlim(start_time, end_time)

    plt.tight_layout()
    plt.show()

def plot_single_map(data: dict[int, float], label="Value", x_limits: Optional[tuple[int, int]] = None):
    # Sort items by key
    sorted_items = sorted(data.items())

    # Convert keys from timestamp in ms to datetime
    x = [datetime.fromtimestamp(k / 1000) for k, v in sorted_items]
    y = [v for k, v in sorted_items]

    plt.figure(figsize=(12, 6))
    plt.plot(x, y, marker='o', label=label)

    plt.xlabel('Time')
    plt.ylabel('Value')
    plt.title(f'{label} Over Time')
    plt.legend()
    plt.grid(True)
    plt.xticks(rotation=45)

    # Apply x-axis limits if provided
    if x_limits:
        start_time = datetime.fromtimestamp(x_limits[0] / 1000)
        end_time = datetime.fromtimestamp(x_limits[1] / 1000)
        plt.xlim(start_time, end_time)

    plt.tight_layout()
    plt.show()