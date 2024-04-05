#!/usr/bin/env bash

if [ $# -ne 1 ]; then
    echo "Simulation Usage: $0 <record_stage>"
    exit 1
fi

record_stage=$1
dataset_1000k="graphBIG/dataset/LDBC/output-1000k/"

if [[ -z "$record_stage" ]]; then
    record_stage="0"
fi

./graphBIG/benchmark/bench_triangleCount/tc  --dataset $(realpath "$dataset_1000k") --record_stage $record_stage