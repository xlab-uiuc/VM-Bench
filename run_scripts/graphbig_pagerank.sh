#!/usr/bin/env bash

perf_ctrl_fifo=$1
ack_fifo=$2
dataset_1000k="graphBIG/dataset/LDBC/output-1000k/"

if [[ -n "$perf_ctrl_fifo" || -n "$ack_fifo" ]]; then
    ./graphBIG/benchmark/bench_pageRank/pagerank --dataset $(realpath "$dataset_1000k") --perf_ctrl_fifo $perf_ctrl_fifo --perf_ack_fifo $ack_fifo
else
    ./graphBIG/benchmark/bench_pageRank/pagerank --dataset $(realpath "$dataset_1000k")
fi