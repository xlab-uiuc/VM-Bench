#!/bin/bash

perf_ctrl_fifo=$1
ack_fifo=$2

# time=0 means run without limit
sysbench_command="sysbench/src/sysbench memory --memory-block-size=64G --memory-total-size=200G --time=0 run"
if [[ -n "$perf_ctrl_fifo" && -n "$ack_fifo" ]]; then
    $sysbench_command --perf_ctl_fifo=$perf_ctrl_fifo --perf_ack_fifo=$ack_fifo
else
    $sysbench_command
fi

# --time=60