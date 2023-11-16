#!/usr/bin/bash

# set -x
BASEDIR=`pwd`

PERF_CPU=4
COMMAND_CPU=8
PERF_PATH=/home/siyuan/linux_5.15_vanilla/tools/perf/perf
PERF_FREQ=70000

KERNEL_NAME=`uname -r`

OUT_FOLDER="paper_results/${KERNEL_NAME}/FlameGraph"
mkdir -p $OUT_FOLDER

THP_CONFIG="no_thp_support"
thp_file="/sys/kernel/mm/transparent_hugepage/enabled"

# Check if the file exists
if [[ -f $thp_file ]]; then
    # Read the content of the file
    content=$(cat $thp_file)
    
    # Check if 'always' or 'madvise' is active (indicated by the [brackets])
    if [[ $content == *"[always]"* ]]; then
        THP_CONFIG="THP_always"
    elif [[ $content == *"[madvise]"* ]]; then
        THP_CONFIG="THP_madvise"
    elif [[ $content == *"[never]"* ]]; then
        THP_CONFIG="THP_never"
    else
        echo "Unable to determine the status of Transparent Huge Pages."
    fi
else
    echo "Transparent Huge Pages is not supported on this system."
fi

FILE_PREFIX=${KERNEL_NAME}_${THP_CONFIG}

BENCH_NAMES=(
    "graphbig_bc" 
    "graphbig_bfs" 
    "graphbig_dfs" 
    "graphbig_dc" 
    "graphbig_sssp" 
    "graphbig_cc" 
    "graphbig_tc" 
    "graphbig_pagerank" 
    "sysbench" 
    "gups"
    "mummer"
)


PID_GREP_KEYWORDS=(
    "graphBIG/benchmark/bench_betweennessCentr/bc "
    "graphBIG/benchmark/bench_BFS/bfs"
    "graphBIG/benchmark/bench_DFS/dfs"
    "graphBIG/benchmark/bench_degreeCentr/dc"
    "graphBIG/benchmark/bench_shortestPath/sssp"
    "graphBIG/benchmark/bench_connectedComp/connectedcomponent"
    "graphBIG/benchmark/bench_triangleCount/tc"
    "graphBIG/benchmark/bench_pageRank/pagerank"
    "sysbench/src/sysbench"
    "gups_vanilla"
    "\d\s+\./MUMmer/mummer"
)

# TODO bind BENCH_NAMES and KEYWORDS together
KEYWORDS=(
    "bc;"
    "bfs;"
    "dfs;"
    "dc;"
    "sssp;"
    "connectedcomponent;"
    "tc;"
    "pagerank;"
    "sysbench;"
    "gups_vanilla;"
    "mummer;"
)

# set large sampling frequency
sudo bash -c "echo $PERF_FREQ > /sys/kernel/mm/transparent_hugepage/enabled"

for ((i=0; i<${#BENCH_NAMES[@]}; i++)); do
    bench=${BENCH_NAMES[$i]}
    keyword=${KEYWORDS[$i]}
    
    echo "${bench} - ${keyword}"

    for j in {1..5}
    do
        file_prefix_bench=${FILE_PREFIX}_${bench}_iter${j}
        echo $file_prefix_bench

        sudo rm perf.data
        sudo taskset -c $PERF_CPU $PERF_PATH record -F $PERF_FREQ -a -g -- taskset -c $COMMAND_CPU ${BASEDIR}/run_scripts/${bench}.sh

        sudo $PERF_PATH script > ${OUT_FOLDER}/${file_prefix_bench}_out.perf

        ${BASEDIR}/FlameGraph/stackcollapse-perf.pl ${OUT_FOLDER}/${file_prefix_bench}_out.perf >  ${OUT_FOLDER}/${file_prefix_bench}_out.folded
        rg "^$keyword" ${OUT_FOLDER}/${file_prefix_bench}_out.folded > ${OUT_FOLDER}/${file_prefix_bench}_out_selected.folded

        ${BASEDIR}/FlameGraph/flamegraph.pl ${OUT_FOLDER}/${file_prefix_bench}_out_selected.folded > ${OUT_FOLDER}/${file_prefix_bench}_bench.svg

        # remove large intermediate file
        sudo rm ${OUT_FOLDER}/${file_prefix_bench}_out.perf

    done
done

