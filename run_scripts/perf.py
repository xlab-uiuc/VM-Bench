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

PERF_PATH = "/home/schai/linux_gen_x86/tools/perf/perf"
RUN_TIMES = 5
benchmarks = {
    # bench_name, relative bench script path, times, output path
    "Graph - BC"  : ("graphbig_bc.sh"       , RUN_TIMES, OUTPUT_DIR + "graphbig_bc.perf"),
    "Graph - BFS" : ("graphbig_bfs.sh"      , RUN_TIMES, OUTPUT_DIR + "graphbig_bfs.perf"),
    "Graph - DFS" : ("graphbig_dfs.sh"      , RUN_TIMES, OUTPUT_DIR + "graphbig_dfs.perf"),
    "Graph - DC"  : ("graphbig_dc.sh"       , RUN_TIMES, OUTPUT_DIR + "graphbig_dc.perf"),
    "Graph - SSSP": ("graphbig_sssp.sh"     , RUN_TIMES, OUTPUT_DIR + "graphbig_sssp.perf"),
    "Graph - CC"  : ("graphbig_cc.sh"       , RUN_TIMES, OUTPUT_DIR + "graphbig_cc.perf"),
    "Graph - TC"  : ("graphbig_tc.sh"       , RUN_TIMES, OUTPUT_DIR + "graphbig_tc.perf"),
    "Graph - PR"  : ("graphbig_pagerank.sh" , RUN_TIMES, OUTPUT_DIR + "graphbig_pagerank.perf"),
    "sysbench"    : ("sysbench.sh"          , RUN_TIMES, OUTPUT_DIR + "sysbench.perf"),
    "mem_test"    : ("mem_test.sh"          , RUN_TIMES, OUTPUT_DIR + "mem_test.perf"),
    "gups"        : ("gups.sh"              , RUN_TIMES, OUTPUT_DIR + "gups.perf"),
    "mummer"      : ("mummer.sh"            , RUN_TIMES, OUTPUT_DIR + "mummer.perf"),
}


def run_perf(command, outpath):
    perf_cpu = "1"
    command_cpu = "5"
    cmd = [
        "sudo", "taskset", "-c", perf_cpu, PERF_PATH, "stat",
        "--event=dtlb_load_misses.walk_pending,dtlb_store_misses.walk_pending,itlb_misses.walk_pending,dtlb_load_misses.walk_completed,dtlb_store_misses.walk_completed,itlb_misses.walk_completed,page-faults",
        "-C", command_cpu, "-I", "1000", "-o",
        outpath, "--", "taskset", "-c", command_cpu, command
    ]
    print(' '.join(cmd))
    r = subprocess.run(cmd, capture_output=True)
    assert r.returncode == 0

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

def get_result_filename():
    kernel = get_kernel_version()
    thp_config = get_thp_config()

    d = datetime.datetime.now()
    timestamp = d.strftime("%Y-%m-%d-%H-%M-%S")

    return f'./{kernel}_{thp_config}_{timestamp}.csv'

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

def perf(bench_list):
    for name, info in bench_list.items():
        bench_path, times, output_path = info
        bench_real_path = os.path.join(SCRIPT_DIR, bench_path)

        print(f"Running {name} for {times} times...")

        total_load_time = 0.0
        total_run_time = 0.0
        
        latencies = []
        n_pfs = []
        for t in range(times):
            print(f"{t + 1}...", flush=True, end='')
            output = run_perf(bench_real_path, output_path).decode('utf-8')

            l, n_pf = calc_average_page_walk_latency(output_path)
            print(l)
            latencies.append(l)
            n_pfs.append(n_pf)
        

        print("")
        avg_latency = sum(latencies) / len(latencies)
        avg_n_pf = sum(n_pfs) / len(n_pfs)
        print(f"Average latency: {avg_latency}")
        print(f"Average page faults: {avg_n_pf}")

        with open(FILENAME, 'a') as f:
            f.write(f"{name},{times},{avg_latency}\n")

if __name__ == "__main__":
    FILENAME = get_result_filename()
    Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)

    SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))

    parser = argparse.ArgumentParser(description='A script with flags.')
    parser.add_argument('--benchs', nargs='*', default=[])
    args = parser.parse_args()
    bench_names = args.benchs

    print(bench_names)
    if len(bench_names) == 0:
        perf(bench_list=benchmarks)
    else:
        bench_list = {}
        for name in bench_names:
            if name in benchmarks:
                bench_list[name] = benchmarks[name]
            else:
                print(f"Unknown benchmark: {name}")
        perf(bench_list=bench_list)
