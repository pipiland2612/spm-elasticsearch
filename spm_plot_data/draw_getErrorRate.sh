#!/bin/bash

#List of services that has error: [driver, redis, frontend]
service=${1:-redis}  # Default to 'redis' if no argument is provided
#current_timestamp=$(($(date +%s) * 1000))

curl --request GET \
  --url http://localhost:9200/jaeger-main-jaeger-span-2025-06-07/_search \
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


curl --request GET \
  --url http://localhost:9200/jaeger-main-jaeger-span-2025-06-07/_search \
  --header 'content-type: application/json' \
  --header 'host: localhost:9200' \
  --header 'user-agent: vscode-restclient' \
  --data @- <<EOF | jq . > ./json/es_getErrorRate.json
{
  "size": 10,
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
                  {"term": {"tags.key": "span.kind"}},
                  {"term": {"tags.value": "server" }}]}}}
        },
        {
          "nested": {
            "path": "tags",
            "query": {
              "bool": {
                "must": [
                  {"term": {"tags.key": "error"}},
                  {"term": {"tags.value": true}}]}}}
        },
        {
          "range": {
            "startTimeMillis": {
              "gte": "now-6h",
              "lte": "now",
              "format": "epoch_millis"
            }}}]}
  },
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
          "cumulative_sum": {
            "buckets_path": "_count"
          }
        },
        "rate_per_second": {
          "moving_fn": {
            "script": {
              "source": "if (values == null || values.length < 2) {  return 0.0; } double windowSizeSeconds = values.length * params.interval_ms / 1000.0; double firstVal = values[0];\ndouble lastVal = values[values.length - 1]; return (lastVal - firstVal) / windowSizeSeconds;",
              "lang": "painless",
              "params": {
                "window": 10,
                "interval_ms": 60000
              }
            },
            "buckets_path": "cumulative_requests",
            "window": 10 }}}}}
}
EOF

python3 ./python/plot_getErrorRate.py