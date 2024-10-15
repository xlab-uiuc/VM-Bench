#!/usr/bin/env bash


[ ! $1 ] && OUTPUT_FOLDER="output" || OUTPUT_FOLDER=$1

kernel=`uname -r`
content=`cat /sys/kernel/mm/transparent_hugepage/enabled`

if [[ $content == *"[always]"* ]]; then
    THP_CONFIG="THP_always"
elif [[ $content == *"[madvise]"* ]]; then
    THP_CONFIG="THP_madvise"
elif [[ $content == *"[never]"* ]]; then
    THP_CONFIG="THP_never"
else
    echo "Unable to determine the status of Transparent Huge Pages."
fi

timestamp=`date +%Y-%m-%d_%H-%M-%S`
OUTPUT_FOLDER=paper_results/$OUTPUT_FOLDER-${kernel}-${THP_CONFIG}-${timestamp}
echo "Output folder: $OUTPUT_FOLDER"
mkdir -p $OUTPUT_FOLDER
chmod +666 $OUTPUT_FOLDER


ITERATION=7
for ((i=0;i<$ITERATION;i++)); do
    # sudo numactl --cpunodebind=0 --membind=0 --physcpubind=0,1,2,3,4,5,6,7 ./workloads/bin/bench_redis_st 2>&1 | tee $OUTPUT_FOLDER/redis_${kernel}_${THP_CONFIG}_standalone_iter${i}.txt
    sudo taskset -ac 8 ./workloads/bin/bench_redis_st 2>&1 | tee $OUTPUT_FOLDER/redis_${kernel}_${THP_CONFIG}_standalone_iter${i}.txt
done

