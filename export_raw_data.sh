#!/bin/bash

### Prepare the environment with necessary tools
# brew install jq dasel

# Echo header for CSV output
echo 'spanID,operationName,startTimeMillis,duration'

curl --request GET \
  --url http://localhost:9200/jaeger-main-jaeger-span-2025-05-30/_search \
 -s  --header 'content-type: application/json' \
  --header 'host: localhost:9200' \
  --header 'user-agent: vscode-restclient' \
  --data '{"size": 10000,"_source": ["spanID","operationName","duration","startTimeMillis"],"query": {"bool": {"filter": [{"term": {"process.serviceName": "redis"}},{"nested": {"path": "tags","query": {"bool": {"must": [{"term": {"tags.key": "span.kind"}},{"term": {"tags.value": "server"}}]}}}},{"range": {"startTimeMillis": {"gte": "now-20m","lte": "now","format": "epoch_millis"}}}]}}}'  \
  | jq '.hits.hits[] | ._source' \
  | dasel -r json -w csv | grep -v duration