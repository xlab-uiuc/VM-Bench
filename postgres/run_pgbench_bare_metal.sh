#!/bin/bash

# Preparation

# sudo apt install postgresql-14


# sudo su postgres
# PATH=$PATH:/usr/lib/postgresql/14/bin/
# initdb -d /disk/ssd1/siyuan_pgsql/data

# Update postgresql.conf
# references https://www.postgresql.org/docs/current/runtime-config-resource.html

# initialize database, postgres is the default database name


# start and run
export PATH=$PATH:/usr/lib/postgresql/14/bin/
directory=/disk/ssd1/siyuan_pgsql/data




# TODO get all of this in a preparation script
# init after start database
# pgbench --initialize --scale 2000 postgres


PARENT_FOLDER="postgres_results"

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
OUTPUT_FOLDER=$PARENT_FOLDER/${kernel}-${THP_CONFIG}-${timestamp}
echo "Output folder: $OUTPUT_FOLDER"
mkdir -p $OUTPUT_FOLDER


ITERATION=5
for ((i=0;i<$ITERATION;i++));
do
    numactl --cpunodebind=0 --membind=0 --physcpubind=0,1,2,3,4,5,6,7 pg_ctl start -D $directory -l $directory/serverlog
    echo "RUN PHASE"

    sleep 2
    # 26.9GB, 800
    taskset --cpu-list 9-15 pgbench --client=10 --time=800 2>&1 | tee $OUTPUT_FOLDER/workload${WORKLOAD}_Load_iter${i}.txt

    echo "Running..."
    sleep 2

    taskset --cpu-list 9-15 pgbench --client=10 --time=100 2>&1 | tee $OUTPUT_FOLDER/workload${WORKLOAD}_Run_iter${i}.txt

    pg_ctl stop -D $directory
done

sleep 1
echo "Output folder: $OUTPUT_FOLDER"

python3 collect_postgres.py --folder $OUTPUT_FOLDER

sleep 1
# pgbench --client=10 --time=120

# sleep 30
# 