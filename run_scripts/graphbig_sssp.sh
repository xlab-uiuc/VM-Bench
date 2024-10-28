#!/usr/bin/env bash

perf_ctrl_fifo=$1
ack_fifo=$2
record_stage=$3
dataset_1000k="graphBIG/dataset/LDBC/output-1000k/"

if [[ -z "$record_stage" ]]; then
    record_stage="0"
fi

if [[ -n "$perf_ctrl_fifo" && -n "$ack_fifo" ]]; then
    ./graphBIG/benchmark/bench_shortestPath/sssp --dataset $(realpath "$dataset_1000k") --perf_ctrl_fifo $perf_ctrl_fifo --perf_ack_fifo $ack_fifo --record_stage $record_stage
else
    ./graphBIG/benchmark/bench_shortestPath/sssp --dataset $(realpath "$dataset_1000k")
fi
