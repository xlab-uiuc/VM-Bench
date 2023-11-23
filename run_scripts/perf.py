#!/usr/bin/env python3
import argparse
import os
import re
import subprocess
import datetime
from pathlib import Path
from typing import NamedTuple

FILENAME = ''
SCRIPT_DIR = ''
OUTPUT_DIR = 'perf_results/'

# PERF_PATH = "/usr/bin/perf"
PERF_PATH = "/home/siyuan/linux_5.15_vanilla/tools/perf/perf"
RUN_TIMES = 7
KERNEL_VERSION = ""

PERF_CTRL_FIFO = "perf_ctrl_fifo"
PERF_ACK_FIFO = "perf_ack_fifo"
def select_benchmarks(bench_names, benches_to_run):
    if len(benches_to_run) == 0:
        return bench_names
    
    selected_bench = []
    for bench in benches_to_run:
        if bench in bench_names:
            selected_bench.append(bench)
        else:
            print(f"Unknown benchmark: {bench}")

    return selected_bench

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

def get_app_benchs(benches_to_run):
    app_benchs = {}

    bench_names = [
        # "graphbig_bc",
        "graphbig_bfs",
        "graphbig_dfs",
        "graphbig_dc",
        "graphbig_sssp",
        "graphbig_cc",
        "graphbig_tc",
        "graphbig_pagerank",
        "sysbench",
        "gups",
        # "mummer",
    ]

    selected_bench = select_benchmarks(bench_names, benches_to_run)
    print("Running benchmarks: ", selected_bench)

    mkfifo(PERF_CTRL_FIFO)
    mkfifo(PERF_ACK_FIFO)
    for bench in selected_bench:
        app_benchs[f"APP {bench}"] = (
            [os.path.join(SCRIPT_DIR, bench + '.sh'), 
                PERF_CTRL_FIFO, PERF_ACK_FIFO
            ],
            RUN_TIMES,
            os.path.join(bench + '.perf'))

    print(app_benchs)
    return app_benchs


def get_lebenchs(benches_to_run):

    bench_names = [
        "ref",
        "cpu",
        "getpid",
        "context_switch",
        "send",
        "recv",
        "big_send",
        "big_recv",
        "fork",
        "thr_create",
        "big_fork",
        "huge_fork",
        "small_write",
        "small_read",
        "small_mmap",
        "small_munmap",
        "small_page_fault",
        "mid_write",
        "mid_read",
        "mid_mmap",
        "mid_munmap",
        "mid_page_fault",
        "big_write",
        "big_read",
        "big_mmap",
        "big_munmap",
        "big_page_fault",
        "huge_write",
        "huge_read",
        "huge_mmap",
        "huge_munmap",
        "huge_page_fault",
        "select",
        "poll",
        "epoll",
        "select_big",
        "poll_big",
        "epoll_big",
    ]

    selected_bench = select_benchmarks(bench_names, benches_to_run)
    print("Running benchmarks: ", selected_bench)

    mkfifo(PERF_CTRL_FIFO)
    mkfifo(PERF_ACK_FIFO)

    lebenchs = {}
    OS_EVAL_PATAH = "LEBench/TEST_DIR/OS_Eval"
    for bench_name in selected_bench:
        lebenchs[f"LEBench {bench_name}"] = (
            [OS_EVAL_PATAH, "0", KERNEL_VERSION, bench_name, PERF_CTRL_FIFO, PERF_ACK_FIFO], RUN_TIMES, f"LEBench_{bench_name}.perf")

    return lebenchs


def run_perf(command, outpath, t):
    perf_cpu = "4"
    command_cpu = "8"
    
    # stat_freq = "100" if "LEBench" in command[0] else "400"
    
    cmd = [
        "sudo", "taskset", "-ac", perf_cpu, PERF_PATH, "stat",
        "--event=dtlb_load_misses.walk_pending,dtlb_store_misses.walk_pending,itlb_misses.walk_pending,dtlb_load_misses.walk_completed,dtlb_store_misses.walk_completed,itlb_misses.walk_completed,page-faults",
        "-C", command_cpu, "-I", "200", "-o",
        outpath]

    # TODO: mummer benchmarks measures entire system performance, so we don't support fine grained perf control
    if not "mummer" in command[0]:        
        cmd += ["--delay=-1", "--control=" f"fifo:{PERF_CTRL_FIFO},{PERF_ACK_FIFO}"]

    cmd += ["--", "taskset", "-ac", command_cpu] + command
    if (t == 0):
        print(command)
        print(' '.join(cmd))
    
    if "LEBench" in command[0]:
        if os.path.exists("test_file.txt"):
            os.remove("test_file.txt")
    
    r = subprocess.run(cmd, capture_output=True)
    assert r.returncode == 0

    if "LEBench" in command[0]:
        os.remove("test_file.txt")
    
    return r.stdout

def get_kernel_version():
    try:
        output = subprocess.check_output(["uname", "-r"], universal_newlines=True)
        return output.strip()
    except subprocess.CalledProcessError as e:
        print(f"Error occurred: {e}")
        return None

def get_thp_config():
    try:
        output = subprocess.check_output(["cat", "/sys/kernel/mm/transparent_hugepage/enabled"], universal_newlines=True)
        if "[always]" in output.strip():
            return "THP_always"
        elif "[madvise]" in output.strip():
            return "THP_madvise"
        elif "[never]" in output.strip():
            return "THP_never"
        else:
            return "no_thp_support"
    except subprocess.CalledProcessError as e:
        print(f"Error occurred: {e}")
        return "no_thp_support"

def get_result_filename(bench_suite):
    kernel = get_kernel_version()
    thp_config = get_thp_config()

    d = datetime.datetime.now()
    timestamp = d.strftime("%Y-%m-%d-%H-%M-%S")

    return f'paper_results/{kernel}/{kernel}_{thp_config}_{bench_suite}_latency_{timestamp}.csv'

def calc_average_page_walk_latency(perf_result):
    EVENT_COUNT_POS = 1
    EVENT_NAME_POS = 2
    total_pending = 0.0
    total_walked = 0
    total_pf = 0
    with open(perf_result) as file:
        for line in file:
            tokens = line.split()
            if len(tokens) >= 3:
                if "walk_pending" in tokens[EVENT_NAME_POS]:
                    # remove comma in strings
                    count_str = tokens[EVENT_COUNT_POS].replace(',', '')
                    total_pending += float(count_str)
                if "walk_completed" in tokens[EVENT_NAME_POS]:
                    count_str = tokens[EVENT_COUNT_POS].replace(',', '')
                    total_walked += float(count_str)
                if "page-faults" in tokens[EVENT_NAME_POS]:
                    count_str = tokens[EVENT_COUNT_POS].replace(',', '')
                    total_pf += float(count_str)

    print("total_pending: ", total_pending, "total_walked: ", total_walked, "total_pf: ", total_pf)
    avg_walk_latency = total_pending / total_walked

    return avg_walk_latency, total_pf


def intit_output_csv(times):
    pgwalk_latency_iter_times = [
        "pgwalk_latency_iter_" + str(i) for i in range(times)]
    pf_iter_times = ["pf_iter_" + str(i) for i in range(times)]

    pgwalk_latency_iter_str = ",".join(pgwalk_latency_iter_times)
    pf_iter_str = ",".join(pf_iter_times)

    with open(FILENAME, 'w') as f:
        f.write(
            f"name,times,{pgwalk_latency_iter_str},avg_latency,{pf_iter_str},avg_pf\n")


def get_perf_output_folder(kernel, thp_config):
    return f"perf_results/{kernel}/{thp_config}/"


def perf(bench_list):
    intit_output_csv(RUN_TIMES)
    perf_out_folder = get_perf_output_folder(get_kernel_version(), get_thp_config())
    
    Path(perf_out_folder).mkdir(parents=True, exist_ok=True)
    for name, info in bench_list.items():
        bench_cmd, times, output_path = info
        # bench_real_path = os.path.join(SCRIPT_DIR, bench_path)
        
        print(f"Running {name} for {times} times...")

        total_load_time = 0.0
        total_run_time = 0.0
        
        latencies = []
        n_pfs = []
        for t in range(times):
            print(f"{t + 1}...", flush=True, end='')
            cur_output_path = os.path.join(perf_out_folder, output_path + f"_{t}")            

            output = run_perf(bench_cmd, cur_output_path, t).decode('utf-8')

            l, n_pf = calc_average_page_walk_latency(cur_output_path)
            print(l)
            latencies.append(l)
            n_pfs.append(n_pf)
        

        print("")
        avg_latency = sum(latencies) / len(latencies)
        avg_n_pf = sum(n_pfs) / len(n_pfs)
        print(f"Average latency: {avg_latency}")
        print(f"Average page faults: {avg_n_pf}")

        with open(FILENAME, 'a') as f:
            latencies_str = ",".join(map(str, latencies))
            n_pfs_str = ",".join(map(str, n_pfs))
            f.write(f"{name},{times},{latencies_str},{avg_latency},{n_pfs_str},{avg_n_pf}\n")

if __name__ == "__main__":
   
    Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)
    
    SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))
    KERNEL_VERSION = get_kernel_version()

    parser = argparse.ArgumentParser(description='A script with flags.')
    parser.add_argument('--bench_suite', type=str, help='The benchmark suite to use')
    parser.add_argument('--benchs', nargs='*', default=[])
    args = parser.parse_args()
    
    bench_suite = args.bench_suite
    benches_to_run = args.benchs

    FILENAME = get_result_filename(bench_suite)
    Path(os.path.dirname(FILENAME)).mkdir(parents=True, exist_ok=True)
    
    if (bench_suite == "LEBench"):
        perf(bench_list=get_lebenchs(benches_to_run))
    elif (bench_suite == "app"):
        perf(bench_list=get_app_benchs(benches_to_run))
    else:
        print("Unknown benchmark suite: ", bench_suite)

    print('Resuls are saved to: ', FILENAME)
    
    clean_fifo(PERF_CTRL_FIFO)
    clean_fifo(PERF_ACK_FIFO)
