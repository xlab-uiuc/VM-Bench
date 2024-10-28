#!/usr/bin/env bash
# See https://github.com/alexandermerritt/gups for parameter setup

perf_ctrl_fifo=$1
ack_fifo=$2
record_stage=$3

if [[ -n "$perf_ctrl_fifo" && -n "$ack_fifo" ]]; then
    ./gups/gups_vanilla 33 1024 1000000 $perf_ctrl_fifo $ack_fifo $record_stage
else
    ./gups/gups_vanilla 33 1024 1000000
fi

# 33
# ./gups_vanilla 20 1000 1024;

# ./gups_vanilla 35 1000 1024

