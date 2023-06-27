#!/usr/bin/env bash

BASEDIR=`pwd`
# dataset="graphBIG/dataset/small/"
dataset_1000k="graphBIG/dataset/LDBC/output-1000k/"
run_1000k() {
	"$1" --dataset $(realpath "$dataset_1000k")
}

dataset_10k="graphBIG/dataset/LDBC/output-10k/"
run_10k() {
	"$1" --dataset $(realpath "$dataset_10k")
}

run_10k ./graphBIG/benchmark/bench_betweennessCentr/bc 
run_1000k ./graphBIG/benchmark/bench_BFS/bfs
run_1000k ./graphBIG/benchmark/bench_DFS/dfs
run_1000k ./graphBIG/benchmark/bench_degreeCentr/dc
run_1000k ./graphBIG/benchmark/bench_shortestPath/sssp
run_1000k ./graphBIG/benchmark/bench_connectedComp/connectedcomponent
run_1000k ./graphBIG/benchmark/bench_triangleCount/tc
run_1000k ./graphBIG/benchmark/bench_pageRank/pagerank


cd $BASEDIR
./run_scripts/gups.sh
./run_scripts/mummer.sh
./run_scripts/sysbench.sh
