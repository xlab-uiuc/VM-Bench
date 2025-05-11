#!/usr/bin/env bash

result_dir="ae_result/${USER}"

mkdir -p $result_dir

KERNEL_NAME=`uname -r`
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

bench_out="$result_dir/${KERNEL_NAME}_${THP_CONFIG}_app.csv"

python3 run_scripts/bench_ae.py --out $bench_out

sleep 5

echo "starting Real applications"

redis_folder="${result_dir}/redis_${KERNEL_NAME}_${THP_CONFIG}/"
./run_scripts/redis_ae.sh ${redis_folder}
python3 parse_real_bench.py --folder ${redis_folder}
sleep 5

postgres_folder="${result_dir}/postgres_${KERNEL_NAME}_${THP_CONFIG}/"
./run_scripts/postgres_st_ae.sh ${postgres_folder}
python3 parse_real_bench.py --folder ${postgres_folder}

sleep 5
memcached_folder="${result_dir}/memcached_${KERNEL_NAME}_${THP_CONFIG}/"
./run_scripts/memcached_st_ae.sh ${memcached_folder}
python3 parse_real_bench.py --folder ${memcached_folder}

sleep 2


echo "Benchmarking completed. Results saved to $bench_out"
echo "Redis benchmark done. Output folder: $redis_folder"
echo "Postgres benchmark done. Output folder: $postgres_folder"
echo "Memcached benchmark done. Output folder: $memcached_folder"