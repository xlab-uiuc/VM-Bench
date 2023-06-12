#!/usr/bin/env bash


# dataset="graphBIG/dataset/small/"
dataset_100k="graphBIG/dataset/LDBC/output-10k/"
run_10k() {
	"$1" --dataset $(realpath "$dataset_10k")
}

run_10k ./graphBIG/benchmark/bench_betweennessCentr/bc 
