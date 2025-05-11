#!/usr/bin/env python3
import argparse
import os
import re
import subprocess
import datetime
from typing import NamedTuple

import numpy as np
import pandas as pd

RUNTIMES=2
benchmarks_global = {
    # bench_name, relative bench script path, times, regex of the loadtime, regex of the runtime
    # "Graph - BC"  : ("./graphbig_bc.sh"       , RUNTIMES, r"time: (.*) sec", r"time: (.*) sec\n="),
    "Graph - BFS": ("./graphbig_bfs.sh", RUNTIMES, r"time: (.*) sec", r"time: (.*) sec\n="),
    "Graph - DFS": ("./graphbig_dfs.sh", RUNTIMES, r"time: (.*) sec", r"time: (.*) sec\n="),
    "Graph - DC"  : ("./graphbig_dc.sh"       , RUNTIMES, r"time: (.*) sec", r"time: (.*) sec\n="),
    "Graph - SSSP": ("./graphbig_sssp.sh"     , RUNTIMES, r"time: (.*) sec", r"time: (.*) sec\n="),
    "Graph - CC"  : ("./graphbig_cc.sh"       , RUNTIMES, r"time: (.*) sec", r"time: (.*) sec\n="),
    "Graph - TC"  : ("./graphbig_tc.sh"       , RUNTIMES, r"time: (.*) sec", r"time: (.*) sec\n="),
    "Graph - PR"  : ("./graphbig_pagerank.sh" , RUNTIMES, r"time: (.*) sec", r"time: (.*) sec\n="),
    "sysbench"    : ("./sysbench.sh"          , RUNTIMES, None             , r"time elapsed:\s+(.*)s"),
    "gups"        : ("./gups.sh"              , RUNTIMES, None             , r"Update time \(secs\):    (.*)"),
    # # "gups"        : ("./gups.sh"              , RUNTIMES, None             , r"Gups:  (.*)"),
    # "mummer"      : ("./mummer.sh"            , RUNTIMES, None             , r"real (.*) user"),
}


FILENAME = ""
SCRIPT_DIR = ""

def get_app_benchs(benches_to_run):
    if len(benches_to_run) == 0:
        return benchmarks_global
    else:
        return {k: v for k, v in benchmarks_global.items() if k in benches_to_run}


def run_command(cmd):
    command_cpu = "8"

    # cmd_list = ["sudo", "taskset", "-ac", command_cpu, cmd]
    cmd_list = ["taskset", "-ac", command_cpu, cmd]
    print(' '.join(cmd_list))
    r = subprocess.run(
        cmd_list, capture_output=True
    )

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
        output = subprocess.check_output(
            ["cat", "/sys/kernel/mm/transparent_hugepage/enabled"],
            universal_newlines=True,
        )
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

    return f"paper_results/{kernel}/{kernel}_{thp_config}_app_{timestamp}.csv"


def get_init_df(times):
    load_iter_times = ["load_time_iter_" + str(i) for i in range(times)]
    run_iter_times = ["run_time_iter_" + str(i) for i in range(times)]

    return pd.DataFrame(
        columns=["name", "times"]
        + load_iter_times
        + ["avg_load_time"]
        + run_iter_times
        + ["avg_run_time"]
    )


def bench(benchmarks):
    to_runs = [k for k, v in benchmarks.items() ]
    print(to_runs)
    df = get_init_df(RUNTIMES)
    for i, (name, info) in enumerate(benchmarks.items()):
        bench_path, times, regex_load_time, regex_run_time = info
        bench_real_path = os.path.join(SCRIPT_DIR, bench_path)

        r_load = r_run = None
        if regex_load_time:
            r_load = re.compile(regex_load_time, re.MULTILINE)
        if regex_run_time:
            r_run = re.compile(regex_run_time, re.MULTILINE)

        print(f"Running {name} for {times} times...")

        # total_load_time = 0.0
        # total_run_time = 0.0
        load_times = []
        run_times = []
        print(r_load, r_run)
        for t in range(times):
            print(f"{t + 1}...", flush=True, end="")
            output = run_command(bench_real_path).decode("utf-8")
            if r_load:
                load_time = float(r_load.search(output).group(1))
                # total_load_time += load_time
            else:
                load_time = np.nan

            if r_run:
                run_time = float(r_run.search(output).group(1))
            else:
                run_time = np.nan

            load_times.append(load_time)
            run_times.append(run_time)

        avg_load_time = sum(load_times) / len(load_times) 
        avg_run_time = sum(run_times) / len(run_times) 

        print("")
        print(f"Average load time: {avg_load_time}")
        print(f"Average run time: {avg_run_time}")

        df.loc[i] = [name, times] + load_times + [avg_load_time] + run_times + [avg_run_time]

        # with open(FILENAME, "a") as f:
        #     f.write(f"{name},{times},{avg_load_time},{avg_run_time}\n")

    print(df)
    df.to_csv(FILENAME, index=False)


if __name__ == "__main__":
    FILENAME = get_result_filename()
    SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))
    print(SCRIPT_DIR)

    parser = argparse.ArgumentParser(description='A script with flags.')
    parser.add_argument('--benchs', nargs='*', default=[])
    parser.add_argument('--out', type=str, default="")
    args = parser.parse_args()

    benches_to_run = args.benchs

    if args.out:
        FILENAME = args.out
    
    bench(get_app_benchs(benches_to_run))

    print(f"Results written to {FILENAME}")
