#!/usr/bin/env bash

BASEDIR=`pwd`

prepare() {
	UTIL_FOLDER=$BASEDIR/run_scripts/util
	
	bash $UTIL_FOLDER/lock_cpu_freq.sh
	bash $UTIL_FOLDER/check_cpu_freq.sh
	bash $UTIL_FOLDER/hyperthread_ctrl.sh 0
	bash $UTIL_FOLDER/numa_balance_ctrl.sh 0
}

quit() {
	UTIL_FOLDER=$BASEDIR/run_scripts/util

	bash $UTIL_FOLDER/unlock_cpu_freq.sh
	bash $UTIL_FOLDER/hyperthread_ctrl.sh 1
	bash $UTIL_FOLDER/numa_balance_ctrl.sh 0

	sudo bash -c "echo madvise > /sys/kernel/mm/transparent_hugepage/enabled"
}

bench_perf_and_breakdown() {
	python3 $BASEDIR/run_scripts/bench.py
	sleep 10
	python3 $BASEDIR/run_scripts/perf.py
	sleep 10
	# note this one requires sudo
	$BASEDIR/run_scripts/run_flame_graph.sh
	sleep 10

	# note this one requires sudo
	$BASEDIR/run_scripts/LEBench.sh
}

prepare

sudo bash -c "echo never > /sys/kernel/mm/transparent_hugepage/enabled"
sleep 10


bench_perf_and_breakdown

# running THP
sudo bash -c "echo always > /sys/kernel/mm/transparent_hugepage/enabled"
sleep 10

bench_perf_and_breakdown

quit
