#!/usr/bin/env bash


# dataset="graphBIG/dataset/small/"
dataset_100k="graphBIG/dataset/LDBC/output-1000k/"
run_1000k() {
	"$1" --dataset $(realpath "$dataset_100k")
}

run_1000k ./graphBIG/benchmark/bench_degreeCentr/dc
