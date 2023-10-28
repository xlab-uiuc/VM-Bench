#!/usr/bin/bash

BASEDIR=`pwd`

PERF_CPU=4
COMMAND_CPU=6
PERF_PATH=/home/schai/linux_gen_x86/tools/perf/perf
PERF_FREQ=10000

BENCH_NAME=graphbig_bfs

${BASEDIR}/run_scripts/${BENCH_NAME}.sh &
BENCH_PID=$!
echo $BENCH_NAME " on " ${BENCH_PID}

$PERF_PATH record -F $PERF_FREQ -p $BENCH_PID -g

$PERF_PATH script > out.perf

${BASEDIR}/FlameGraph/stackcollapse-perf.pl out.perf > out.folded
# sudo taskset, "-c", perf_cpu, PERF_PATH, "stat",
#         "--event=dtlb_load_misses.walk_pending,dtlb_store_misses.walk_pending,itlb_misses.walk_pending,dtlb_load_misses.walk_completed,dtlb_store_misses.walk_completed,itlb_misses.walk_completed,page-faults",
#         "-C", command_cpu, "-I", "1000", "-o",
#         outpath, "--", "taskset", "-c", command_cpu, command

