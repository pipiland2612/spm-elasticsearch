#!/bin/bash

service=${1:-jaeger}  # Default to 'redis' if no argument is provided
current_timestamp=$(($(date +%s) * 1000))
curl "http://localhost:16686/api/metrics/latencies?service=${service}&endTs=${current_timestamp}&lookback=21600000&quantile=0.95&ratePer=600000&spanKind=server&step=60000" \
  -H 'Referer: http://localhost:16686/monitor' \
  -H 'Sec-Fetch-Dest: empty' \
  -H 'Sec-Fetch-Mode: cors' \
  -H 'Sec-Fetch-Site: same-origin' \
  -H 'User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36' \
  -H 'sec-ch-ua: "Google Chrome";v="137", "Chromium";v="137", "Not/A)Brand";v="24"' \
  -H 'sec-ch-ua-mobile: ?0' \
  -H 'sec-ch-ua-platform: "macOS"'| jq . > ./json/spm_getLatencies.json


curl --request GET \
  --url http://localhost:9200/jaeger-main-jaeger-span-2025-06-07/_search \
  --header 'content-type: application/json' \
  --header 'host: localhost:9200' \
  --header 'user-agent: vscode-restclient' \
  --data @- <<EOF | jq . > ./json/es_getLatencies.json
{
  "size": 0,
  "query": {
    "bool": {
      "filter": [
        {
          "term": {
            "process.serviceName": "${service}"
          }
        },
        {
          "nested": {
            "path": "tags",
            "query": {
              "bool": {
                "must": [
                  {
                    "term": {
                      "tags.key": "span.kind"
                    }
                  },
                  {
                    "term": {
                      "tags.value": "server" }}]}}}
        },
        {
          "range": {
            "startTimeMillis": {
              "gte": "now-6h",
              "lte": "now",
              "format": "epoch_millis" }}}]}
  },
  "aggs": {
    "minute_buckets": {
      "date_histogram": {
        "field": "startTimeMillis",
        "fixed_interval": "1m",
        "min_doc_count": 0,
        "extended_bounds": {
          "min": "now-20m",
          "max": "now"
        }
      },
      "aggs": {
        "percentiles_of_bucket": {
          "percentiles": {
            "field": "duration",
            "percents": [
              50, 95
            ]
          }
        },
        "percentiles_of_bucket_of_10m_window": {
          "moving_percentiles": {
            "buckets_path": "percentiles_of_bucket",
            "window": 10 }}}}}
}
EOF

python3 ./python/plot_getLatencies.py