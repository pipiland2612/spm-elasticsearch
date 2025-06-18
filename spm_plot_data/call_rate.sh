#!/bin/bash

service=${1:-customer}  # Default to 'redis' if no argument is provided
current_timestamp=$(($(date +%s) * 1000))
source1="\"if (values == null || values.length < params.window) { return 0.0; } double windowSizeSeconds = params.window * params.interval_ms / 1000.0; double firstVal = values[0]; double lastVal = values[values.length - 1]; return (lastVal - firstVal) / windowSizeSeconds;\""
source2="\"if (values == null || values.length == 0) return 0.0; double windowSizeSeconds = params.window * params.interval_ms / 1000.0; if (values.length >= params.window) { return (values[values.length - 1] - values[0]) / windowSizeSeconds; } double n = values.length, sumX = 0.0, sumY = 0.0, sumXY = 0.0, sumXX = 0.0; for (int i = 0; i < values.length; i++) { double x = i * params.interval_ms / 1000.0, y = values[i]; sumX += x; sumY += y; sumXY += x * y; sumXX += x * x; } return (n * sumXY - sumX * sumY) / (n * sumXX - sumX * sumX);\""
source3="\"if (values == null || values.length < 2) return 0.0; double n = values.length; double sumX = 0.0; double sumY = 0.0; double sumXY = 0.0; double sumX2 = 0.0; for (int i = 0; i < n; i++) { double x = i; double y = values[i]; sumX += x; sumY += y; sumXY += x * y; sumX2 += x * x; } double numerator = n * sumXY - sumX * sumY; double denominator = n * sumX2 - sumX * sumX; if (Math.abs(denominator) < 1e-10) return 0.0; double slopePerBucket = numerator / denominator; double intervalSeconds = params.interval_ms / 1000.0; return slopePerBucket / intervalSeconds;\""


curl "http://localhost:16686/api/metrics/calls?service=${service}&endTs=${current_timestamp}&lookback=3600000&quantile=0.95&ratePer=600000&spanKind=server&step=60000" \
  -H 'Referer: http://localhost:16686/monitor' \
  -H 'Sec-Fetch-Dest: empty' \
  -H 'Sec-Fetch-Mode: cors' \
  -H 'Sec-Fetch-Site: same-origin' \
  -H 'User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36' \
  -H 'sec-ch-ua: "Google Chrome";v="137", "Chromium";v="137", "Not/A)Brand";v="24"' \
  -H 'sec-ch-ua-mobile: ?0' \
  -H 'sec-ch-ua-platform: "macOS"' | jq . > ./json/spm_getCallRate.json


curl --request GET \
  --url http://localhost:9200/jaeger-span-*/_search \
  --header 'content-type: application/json' \
  --header 'host: localhost:9200' \
  --header 'user-agent: vscode-restclient' \
  --data @- <<EOF | jq . > ./json/es_getCallRate.json
{
  "size": 0,
  "query": {
    "bool": {
      "filter": [
        { "term": { "process.serviceName": "${service}" } },
        {
          "nested": {
            "path": "tags",
            "query": {
              "bool": {
                "must": [
                  { "term": { "tags.key": "span.kind" } },
                  { "term": { "tags.value": "server" } }]}}}},
        {
          "range": {
            "startTimeMillis": {
              "gte": "now-1h",
              "lte": "now",
              "format": "epoch_millis"}}}]}},
  "aggs": {
    "requests_per_bucket": {
      "date_histogram": {
        "field": "startTimeMillis",
        "fixed_interval": "60s",
        "min_doc_count": 0,
        "extended_bounds": {
          "min": "now-1h",
          "max": "now"
        }
      },
      "aggs": {
        "cumulative_requests": {
          "cumulative_sum": { "buckets_path": "_count" }
        },
        "rate_per_second": {
          "moving_fn": {
            "script": {
              "source": ${source3},
              "lang": "painless",
              "params": {
                "window": 10,
                "interval_ms": 60000
              }
            },
            "buckets_path": "cumulative_requests",
            "window": 10}}}}}
}
EOF

python3 ./python/plot_getCallRate.py