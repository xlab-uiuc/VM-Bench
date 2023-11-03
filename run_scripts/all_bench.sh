#!/usr/bin/env bash

BASEDIR=`pwd`

# dataset="graphBIG/dataset/small/"
# dataset_1000k="graphBIG/dataset/LDBC/output-1000k/"
# run_1000k() {
# 	"$1" --dataset $(realpath "$dataset_1000k")
# }

# dataset_10k="graphBIG/dataset/LDBC/output-10k/"
# run_10k() {
# 	"$1" --dataset $(realpath "$dataset_10k")
# }

# run_10k ./graphBIG/benchmark/bench_betweennessCentr/bc 
# run_1000k ./graphBIG/benchmark/bench_BFS/bfs
# run_1000k ./graphBIG/benchmark/bench_DFS/dfs
# run_1000k ./graphBIG/benchmark/bench_degreeCentr/dc
# run_1000k ./graphBIG/benchmark/bench_shortestPath/sssp
# run_1000k ./graphBIG/benchmark/bench_connectedComp/connectedcomponent
# run_1000k ./graphBIG/benchmark/bench_triangleCount/tc
# run_1000k ./graphBIG/benchmark/bench_pageRank/pagerank


# cd $BASEDIR
# ./run_scripts/gups.sh
# ./run_scripts/mummer.sh
# ./run_scripts/sysbench.sh

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

prepare

sudo bash -c "echo never > /sys/kernel/mm/transparent_hugepage/enabled"
sleep 10

python3 $BASEDIR/run_scripts/bench.py
sleep 30
python3 $BASEDIR/run_scripts/perf.py

# running THP
sudo bash -c "echo always > /sys/kernel/mm/transparent_hugepage/enabled"
sleep 10

python3 $BASEDIR/run_scripts/bench.py
sleep 30
python3 $BASEDIR/run_scripts/perf.py

quit
