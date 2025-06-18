This repository is where I do the testing for ES query to generate RED metrics directly from traces, this is a issue of Jaeger Project: https://github.com/jaegertracing/jaeger/issues/6641

Step 1: docker compose up

Step 2: cd spm-plot-data

Step 3:
`bash call_rate.sh`

`bash latencies.sh`

`bash error_rate.sh`

`bash mean.sh`

These commands will make curl request and fetch data to Python file where it's been draw and you can see the correlation between the graph get from SPM data and ES query data
