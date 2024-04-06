#!/bin/bash

record_stage=$1
# time=0 means run without limit
sysbench_command="sysbench/src/sysbench memory --memory-block-size=64G --memory-total-size=200G --time=0 run --record_stage=$record_stage"
${sysbench_command}
