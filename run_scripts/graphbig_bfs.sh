#!/usr/bin/env bash
set -x
perf_ctrl_fifo=$1
ack_fifo=$2
# dataset="graphBIG/dataset/small/"
dataset_1000k="graphBIG/dataset/LDBC/output-100k/"
# run_1000k() {
# 	"$1" --dataset $(realpath "$dataset_1000k") --perf_ctrl_fifo $2
# }

# run_1000k ./graphBIG/benchmark/bench_BFS/bfs $perf_ctrl_fifo

if [ -z "$perf_ctrl_fifo" ]; then
    ./graphBIG/benchmark/bench_BFS/bfs --dataset $(realpath "$dataset_1000k")
else
    ./graphBIG/benchmark/bench_BFS/bfs --dataset $(realpath "$dataset_1000k") --perf_ctrl_fifo $perf_ctrl_fifo --perf_ack_fifo $ack_fifo
fi
