import json
import sys
import math
from statistics import mean
from tabulate import tabulate


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

def extract_operation_means_fromSPM(path_to_file):
    with open(path_to_file, "r", encoding="utf-8") as file:
        data = json.load(file)

    result = {}

    for metric in data.get("metrics", []):
        # Extract operation name from labels
        labels = metric.get("labels", [])
        operation = next((label["value"] for label in labels if label["name"] == "operation"), None)

        if operation:
            valid_sum = 0
            nan_count = 0
            total_count = 0

            for point in metric.get("metricPoints", []):
                value = point.get("gaugeValue", {}).get("doubleValue", None)
                total_count += 1
                if value is None or not isinstance(value, (int, float)) or math.isnan(value):
                    nan_count += 1
                else:
                    valid_sum += value

            mean_value = valid_sum / total_count if total_count > 0 else float("nan")
            result[operation] = mean_value

    return result


def draw_comparison_table(dict1, dict2, header1, header2):
    operations = sorted(set(dict1) & set(dict2))

    table = []
    for op in operations:
        row = [
            op,
            round(dict1[op], 4),
            round(dict2[op], 4),
        ]
        table.append(row)

    headers = ["Operation", header1, header2]
    print(tabulate(table, headers=headers, tablefmt="pretty"))

mean_rates_es = compute_mean_rates_callRate("./json/mean_getCallRate.json")
mean_percentiles_es = extract_95th_percentile_means("./json/mean_getLatencies.json")
mean_rates_spm = extract_operation_means_fromSPM("./json/spm_getCallRate.json")
mean_percentiles_spm = extract_operation_means_fromSPM("./json/spm_getLatencies.json")
mean_error_spm = extract_operation_means_fromSPM("./json/spm_getErrorRate.json")

print("\n")
draw_comparison_table(mean_rates_es, mean_rates_spm, "ES_CallRate", "SPM_CallRate")
draw_comparison_table(mean_percentiles_es, mean_percentiles_spm, "ES_Latencies", "SPM_Latencies")