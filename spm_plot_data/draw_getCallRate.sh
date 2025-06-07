#!/bin/bash

service=${1:-customer}  # Default to 'redis' if no argument is provided
current_timestamp=$(($(date +%s) * 1000))

curl "http://localhost:16686/api/metrics/calls?service=${service}&endTs=${current_timestamp}&lookback=21600000&quantile=0.95&ratePer=600000&spanKind=server&step=60000" \
  -H 'Referer: http://localhost:16686/monitor' \
  -H 'Sec-Fetch-Dest: empty' \
  -H 'Sec-Fetch-Mode: cors' \
  -H 'Sec-Fetch-Site: same-origin' \
  -H 'sec-ch-ua: "Chromium";v="136", "Google Chrome";v="136", "Not.A/Brand";v="99"' \
  -H 'sec-ch-ua-mobile: ?0' \
  -H 'sec-ch-ua-platform: "macOS"' | jq . > spm_data.json


curl --request GET \
  --url http://localhost:9200/jaeger-main-jaeger-span-2025-06-07/_search \
  --header 'content-type: application/json' \
  --header 'host: localhost:9200' \
  --header 'user-agent: vscode-restclient' \
  --data @- <<EOF | jq . > ./json/es_data.json
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
              "gte": "now-6h-10m",
              "lte": "now",
              "format": "epoch_millis"}}}]}},
  "aggs": {
    "requests_per_bucket": {
      "date_histogram": {
        "field": "startTimeMillis",
        "fixed_interval": "60s",
        "min_doc_count": 0,
        "extended_bounds": {
          "min": "now-6h-10m",
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
              "source": "if (values == null || values.length < params.window) {  return 0.0; } double windowSizeSeconds = params.window * params.interval_ms / 1000.0; double firstVal = values[0]; double lastVal = values[values.length - 1]; return (lastVal - firstVal) / windowSizeSeconds;",
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

python3 ./python/plot-getCallRate-data.py