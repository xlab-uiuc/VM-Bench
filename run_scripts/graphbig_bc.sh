#!/usr/bin/env bash

set -x
# dataset="graphBIG/dataset/small/"
dataset_10k="graphBIG/dataset/LDBC/output-100k/"

perf_ctrl_fifo=$1
ack_fifo=$2

if [[ -n "$perf_ctrl_fifo" && -n "$ack_fifo" ]]; then
    ./graphBIG/benchmark/bench_betweennessCentr/bc --dataset $(realpath "$dataset_10k") --perf_ctrl_fifo $perf_ctrl_fifo --perf_ack_fifo $ack_fifo
else
    ./graphBIG/benchmark/bench_betweennessCentr/bc --dataset $(realpath "$dataset_10k")
fi