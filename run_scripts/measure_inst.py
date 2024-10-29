import argparse
import os
import subprocess

PERF_CTRL_FIFO = "perf_ctrl_fifo"
PERF_ACK_FIFO = "perf_ack_fifo"

OUTPUT_FOLDER = "inst_perf"

def mkfifo(fifo_path):
    if not os.path.exists(fifo_path):
        # Create the named pipe
        os.mkfifo(fifo_path)
        print(f"Named pipe '{fifo_path}' created.")
    else:
        print(f"Named pipe '{fifo_path}' already exists.")

def clean_fifo(fifo_path):
    if os.path.exists(fifo_path):
        os.remove(fifo_path)
        print(f"Named pipe '{fifo_path}' removed.")
    else:
        print(f"Named pipe '{fifo_path}' does not exist.")
        

def run_perf(command, outpath):
    perf_cpu = "4"
    command_cpu = "8"
    
    # stat_freq = "100" if "LEBench" in command[0] else "400"
    # sudo perf stat -e instructions:u -e instructions:k --delay=-1 --control=fifo:ctl.fifo,ack.fifo \
    # -- taskset -ac 8 /disk/ssd1/rethinkVM_bench/run_scripts/graphbig_bfs.sh ctl.fifo ack.fifo 2 2>&1 | tee ${FOLDER}/bfs_loading_inst_perf_edges_double.txt

    with open(outpath, "w") as log_file:
        cmd = [
            "sudo", "taskset", "-ac", perf_cpu, "perf", "stat", "-e", "instructions:u", "-e", "instructions:k", 
                "--delay=-1", f"--control=fifo:{PERF_CTRL_FIFO},{PERF_ACK_FIFO}", "-C", command_cpu,
                "--",
                "taskset", "-ac", command_cpu
            ]
        if type(command) == str:
            cmd += command.split()  # Split the command into a list
        
        if type(command) == list:
            cmd += command
        
        print(' '.join(cmd))
        log_file.write(' '.join(cmd) + '\n')
        print('save to ', outpath)
        
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True
        )
        
        for line in process.stdout:
            print(line, end="")                 # print to stdout
            log_file.write(line)                # write to the file

        # Ensure the process completes
        process.wait()

def perf(bench_list):
    for bench in bench_list:
        run_perf(bench["command"], bench["outpath"])
    

def get_output_path(bench_info):
    filename = f"{bench_info['workload']}_{bench_info['stage']}_inst_perf.txt"
    return os.path.join(OUTPUT_FOLDER, filename)


def get_bench_info_loading_from_running(bench_info):
    return {
        "workload": bench_info["workload"],
        "command": bench_info["command"].replace("1", "2"),
        "stage": "loading"
    }

def get_redis_bench_info():
    redis_command = f"./workloads/bin/bench_redis_st -- --perf_ctl_fifo {PERF_CTRL_FIFO} --perf_ack_fifo {PERF_ACK_FIFO}"
    
    redis_running = {
        "workload": "redis",
        "command": redis_command,
        "stage": "running"
    }
    
    redis_loading = {
        "workload": "redis",
        "command": redis_command + " " + "--loading-phase",
        "stage": "loading"
    }
    
    return [redis_running, redis_loading]


def get_memcached_bench_info():
    memcached_command = f"./memcached_rethinkvm/memcached --user=root --memory-limit=131000 --key-max 56000000 --running-insertion-ratio=20"    
    memcached_perf_str = f"--perf-ctrl-fifo={PERF_CTRL_FIFO} --perf-ack-fifo={PERF_ACK_FIFO}"
    memcached_running = {
        "workload": "memcached",
        "command": memcached_command + " " + memcached_perf_str + " --record-stage=1",
        "stage": "running"
    }
    
    memcached_loading = {
        "workload": "memcached",
        "command": memcached_command + " " + memcached_perf_str + " --record-stage=2",
        "stage": "loading"
    }
    
    return [memcached_running, memcached_loading]

def get_postgres_bench_info():
    data_path = os.path.abspath("./postgresql-14.13/data")
    bin_path = os.path.abspath("./postgresql-14.13/build_dir/bin/postgres")
    
    postgres_command_12M = f"{bin_path} --single -D {data_path} postgres -R 12000000 -L {PERF_CTRL_FIFO} -A {PERF_ACK_FIFO}"
    
    postgres_running_12M = {
        "workload": "postgres_12M_read",
        "command": ["su", "postgres", "-c", postgres_command_12M],
        "stage": "running"
    }
    
    postgres_loading_12M = {
        "workload": "postgres_12M_read",
        "command": ["su", "postgres", "-c", postgres_command_12M + " -a"],
        "stage": "loading"
    }
    
    postgres_command_17M = f"{bin_path} --single -D {data_path} postgres -R 17000000 -L {PERF_CTRL_FIFO} -A {PERF_ACK_FIFO}"
    postgres_running_17M = {
        "workload": "postgres_17M_read",
        "command": ["su", "postgres", "-c", postgres_command_17M],
        "stage": "running"
    }
    
    postgres_loading_17M = {
        "workload": "postgres_17M_read",
        "command": ["su", "postgres", "-c", postgres_command_17M + " -a"],
        "stage": "loading"
    }
    
    return [postgres_running_12M, postgres_loading_12M, postgres_running_17M, postgres_loading_17M]

def prepare_bench_list():
    
    benchmarks = [
        "graphbig_bfs",
        "graphbig_dfs",
        "graphbig_dc",
        "graphbig_sssp",
        "graphbig_cc",
        "graphbig_tc",
        "graphbig_pagerank",
        "gups",
        "sysbench"
    ]
    
    bench_list = []
    
    for bench in benchmarks:
        bench_info = {
            "workload": bench,
            "command": f"run_scripts/{bench}.sh {PERF_CTRL_FIFO}  {PERF_ACK_FIFO} 1",
            "stage": "running"
        }
        if bench_info:
            bench_list.append(bench_info)
    
    
    
    loading_bench = [get_bench_info_loading_from_running(bench) for bench in bench_list]
    
    bench_list += loading_bench
    
    bench_list += get_redis_bench_info()
    bench_list += get_memcached_bench_info()
    bench_list += get_postgres_bench_info()
    
    for bench in bench_list:
        bench["outpath"] = get_output_path(bench)
    
    return bench_list

    
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='A script with flags.')
    parser.add_argument('--bench_suite', type=str, help='The benchmark suite to use')
    parser.add_argument('--benchs', nargs='*', default=[])
    args = parser.parse_args()
    
    mkfifo(PERF_CTRL_FIFO)
    mkfifo(PERF_ACK_FIFO)

    os.chmod(PERF_CTRL_FIFO, 0o666)
    os.chmod(PERF_CTRL_FIFO, 0o666)
    
    perf(prepare_bench_list())
    
    clean_fifo(PERF_CTRL_FIFO)
    clean_fifo(PERF_ACK_FIFO)