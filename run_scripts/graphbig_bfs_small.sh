#!/usr/bin/env bash
set -x

# `if [ $# -ne 3 ]; then
#     echo "baremetal Usage: $0 <perf_ctrl_fifo> <ack_fifo> <record_stage> (fifo and record)"

#     echo "Usage: $0 <perf_ctrl_fifo> <ack_fifo> <record_stage> (fifo and record)"
#     echo "Usage: $0 <record_stage> (record but not perf)"
#     echo "Usage: $0 (record running phase in simulation but not perf)"
#     exit 1
# fi


perf_ctrl_fifo=$1
ack_fifo=$2
record_stage=$3
dataset_1000k="graphBIG/dataset/LDBC/output-10k/"

if [[ -z "$record_stage" ]]; then
    record_stage="0"
fi

if [[ -n "$perf_ctrl_fifo" && -n "$ack_fifo" ]]; then
    ./graphBIG/benchmark/bench_BFS/bfs --dataset $(realpath "$dataset_1000k") --perf_ctrl_fifo $perf_ctrl_fifo --perf_ack_fifo $ack_fifo --record_stage $record_stage
else
    ./graphBIG/benchmark/bench_BFS/bfs --dataset $(realpath "$dataset_1000k") --record_stage $record_stage
fi
