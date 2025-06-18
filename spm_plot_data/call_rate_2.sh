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
  -H 'sec-ch-ua-platform: "macOS"' | jq . > ./json/spm_getCallRate.json


curl --request GET \
  --url http://localhost:9200/jaeger-main-jaeger-span-2025-06-12/_search \
  --header 'content-type: application/json' \
  --header 'host: localhost:9200' \
  --header 'user-agent: vscode-restclient' \
  --data @- <<EOF | jq . > ./json/es_getCallRate.json
{
  "aggregations": {
    "results_buckets": {
      "aggregations": {
        "date_histogram": {
          "aggregations": {
            "cumulative_requests": {
              "cumulative_sum": {
                "buckets_path": "_count"
              }
            },
            "results": {
              "moving_fn": {
                "buckets_path": "cumulative_requests",
                "script": {
                  "lang": "painless",
                  "params": {
                    "interval_ms": 60000,
                    "window": 10
                  },
                  "source": "if (values == null || values.length < 2) return 0.0;\n\t\tdouble n = values.length; \n\t\tdouble sumX = 0.0;\n\t\tdouble sumY = 0.0;\n\t\tdouble sumXY = 0.0;\n\t\tdouble sumX2 = 0.0;\n\t\tfor (int i = 0; i < n; i++) { \n\t\t\tdouble x = i;\n\t\t\tdouble y = values[i];\n\t\t\tsumX += x;\n\t\t\tsumY += y;\n\t\t\tsumXY += x * y;\n\t\t\tsumX2 += x * x;\n\t\t} \n\t\tdouble numerator = n * sumXY - sumX * sumY;\n\t\tdouble denominator = n * sumX2 - sumX * sumX;\n\t\tif (Math.abs(denominator) < 1e-10) return 0.0;\n\t\tdouble slopePerBucket = numerator / denominator; \n\t\tdouble intervalSeconds = params.interval_ms / 1000.0;\n\t\treturn slopePerBucket / intervalSeconds;"
                },
                "window": 10
              }
            }
          },
          "date_histogram": {
            "extended_bounds": {
              "max": 1750149149758,
              "min": 1750127549758
            },
            "field": "startTimeMillis",
            "fixed_interval": "60000ms",
            "min_doc_count": 0
          }
        }
      },
      "terms": {
        "field": "operationName",
        "size": 10
      }
    }
  },
  "query": {
    "bool": {
      "filter": [
        {
          "terms": {
            "process.serviceName": [
              "frontend"
            ]
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
                    "bool": {
                      "should": {
                        "term": {
                          "tags.value": "server"
                        }
                      }
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
              "from": 1750127249758,
              "include_lower": true,
              "include_upper": true,
              "to": 1750149149758
            }
          }
        }
      ]
    }
  },
  "size": 0
}
EOF

python3 ./python/plot_getCallRate.py