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
  --url http://localhost:9200/jaeger-span-*/_search \
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
          "min": "now-6h",
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

curl --request GET \
  --url http://localhost:9200/jaeger-span-*/_search \
  --header 'content-type: application/json' \
  --header 'host: localhost:9200' \
  --header 'user-agent: vscode-restclient' \
  --data @- <<EOF | jq . > ./json/es_getLatencies2.json
{
  "size": 0,
  "query": {
    "bool": {
      "filter": [
        {
          "term": { "process.serviceName": "${service}" }
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
                      "tags.value": "server"
                    }
                  }
                ]
              }
            }
          }
        },
        {
          "range": {
            "startTimeMillis": {
              "format": "epoch_millis",
              "from": "now-6h",
              "include_lower": true,
              "include_upper": true,
              "to": "now"
            }
          }
        }
      ]
    }
  },
  "aggs": {
    "requests_per_bucket": {
      "date_histogram": {
        "extended_bounds": {
          "max": "now",
          "min": "now-6h"
        },
        "field": "startTimeMillis",
        "fixed_interval": "60000ms",
        "min_doc_count": 0
      },
      "aggs": {
        "percentiles_of_bucket": {
          "percentiles": {
            "field": "duration",
            "percents": [
              95
            ]
          }
        },
        "results": {
          "moving_fn": {
            "buckets_path": "percentiles_of_bucket[95.0]",
            "script": "List f=new ArrayList();double s=0;for(v in values)if(v!=null&&!Double.isNaN(v)){f.add(v);s+=v;}return f.isEmpty()?Double.NaN:(f.get((int)Math.min(Math.ceil(0.95*(f.size()-1)),f.size()-1))*0.7+(s/f.size())*0.3)",
            "window": 10
          }
        }
      }
    }
  }
}
EOF

python3 ./python/plot_getLatencies.py