#!/usr/bin/bash
# small_anony_page_fault

# sudo /home/siyuan/linux_5.15_vanilla/tools/perf/perf stat -e instructions -- ./gups_vanilla 20 1000 1024;
# cd postgresql-14.13/build_dir/bin/

if [ ! -p ctl.fifo ]; then
    mkfifo ctl.fifo
fi

if [ ! -p ack.fifo ]; then
    mkfifo ack.fifo
fi

FOLDER=inst_perf

# sudo perf stat -e instructions -e page-faults --delay=-1 --control=fifo:ctl.fifo,ack.fifo -- su siyuan -c './postgres --single -D /disk/ssd1/siyuan_pgsql_perf/data/ postgres -R 33000 -L ctl.fifo -A ack.fifo'
sudo perf stat -e instructions:u -e instructions:k --delay=-1 --control=fifo:ctl.fifo,ack.fifo \
    -- taskset -ac 8 /disk/ssd1/rethinkVM_bench/run_scripts/graphbig_bfs.sh ctl.fifo ack.fifo 2 2>&1 | tee ${FOLDER}/bfs_loading_inst_perf.txt

sudo perf stat -e instructions:u -e instructions:k --delay=-1 --control=fifo:ctl.fifo,ack.fifo \
    -- taskset -ac 8 /disk/ssd1/rethinkVM_bench/run_scripts/graphbig_bfs.sh ctl.fifo ack.fifo 1 2>&1 | tee ${FOLDER}/bfs_running_inst_perf.txt 


# MEMCACHED_COMMAND="./memcached_rethinkvm/memcached --user=root --memory-limit=131000 --key-max 56000000 --running-insertion 20 --perf-ctrl-fifo=ctl.fifo --perf-ack-fifo=ack.fifo"
# sudo perf stat -e instructions:u -e instructions:k --delay=-1 --control=fifo:ctl.fifo,ack.fifo \
#     -- taskset -ac 8 ${MEMCACHED_COMMAND} --record-stage 2 2>&1 | tee ${FOLDER}/MEMCACHED_loading_inst_perf.txt

# sudo perf stat -e instructions:u -e instructions:k --delay=-1 --control=fifo:ctl.fifo,ack.fifo \
#     -- taskset -ac 8 ${MEMCACHED_COMMAND} --record-stage 1 2>&1 | tee ${FOLDER}/MEMCACHED_running_inst_perf.txt 