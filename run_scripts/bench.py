#!/usr/bin/env python3
import os
import re
import subprocess
import datetime
from typing import NamedTuple

benchmarks = {
    # bench_name, relative bench script path, times, regex of the loadtime, regex of the runtime
    "Graph - BC"  : ("./graphbig_bc.sh"       , 5, r"time: (.*) sec", r"time: (.*) sec\n="),
    "Graph - BFS" : ("./graphbig_bfs.sh"      , 5, r"time: (.*) sec", r"time: (.*) sec\n="),
    "Graph - DFS" : ("./graphbig_dfs.sh"      , 5, r"time: (.*) sec", r"time: (.*) sec\n="),
    "Graph - DC"  : ("./graphbig_dc.sh"       , 5, r"time: (.*) sec", r"time: (.*) sec\n="),
    "Graph - SSSP": ("./graphbig_sssp.sh"     , 5, r"time: (.*) sec", r"time: (.*) sec\n="),
    "Graph - CC"  : ("./graphbig_cc.sh"       , 5, r"time: (.*) sec", r"time: (.*) sec\n="),
    "Graph - TC"  : ("./graphbig_tc.sh"       , 5, r"time: (.*) sec", r"time: (.*) sec\n="),
    "Graph - PR"  : ("./graphbig_pagerank.sh" , 5, r"time: (.*) sec", r"time: (.*) sec\n="),
    "sysbench"    : ("./sysbench.sh"          , 5, None             , r"time elapsed:\s+(.*)s"),
    "gups"        : ("./gups.sh"              , 5, None             , r"Update time \(secs\):    (.*)"),
    # "gups"        : ("./gups.sh"              , 5, None             , r"Gups:  (.*)"),
    "mummer"      : ("./mummer.sh"            , 5, None             , r"real (.*) user"),
}


FILENAME = ''
SCRIPT_DIR = ''

def run_command(cmd):
    r = subprocess.run([cmd], capture_output=True)
    assert r.returncode == 0

    return r.stdout

def get_result_filename():
    kernel = ''
    with open('/proc/cmdline') as f:
        cmdline = f.read()

        if 'vanilla' in cmdline:
            kernel = 'vanila'
        elif 'gen-x86' in cmdline:
            kernel = 'gen-x86'
        else:
            print("Unknown kernel!")
            kernel = 'unknown'

        thp = 'THP_enabled'
        if 'transparent_hugepage=never' in cmdline:
            thp = 'noTHP'

    d = datetime.datetime.now()
    timestamp = d.strftime("%Y-%m-%d-%H-%M-%S")

    return f'./{kernel}_{thp}_{timestamp}.csv'

def bench():
    for name, info in benchmarks.items():
        bench_path, times, regex_load_time, regex_run_time = info
        bench_real_path = os.path.join(SCRIPT_DIR, bench_path)

        r_load = r_run = None
        if regex_load_time:
            r_load = re.compile(regex_load_time, re.MULTILINE)
        if regex_run_time:
            r_run = re.compile(regex_run_time, re.MULTILINE)

        print(f"Running {name} for {times} times...")

        total_load_time = 0.0
        total_run_time = 0.0

        for t in range(times):
            print(f"{t + 1}...", flush=True, end='')
            output = run_command(bench_real_path).decode('utf-8')
            if r_load:
                load_time = float(r_load.search(output).group(1))
                total_load_time += load_time
            if r_run:
                run_time = float(r_run.search(output).group(1))
                total_run_time += run_time

        if total_load_time > 0.0:
            avg_load_time = total_load_time / times
        else:
            avg_load_time = "NA"
        if total_run_time > 0.0:
            avg_run_time = total_run_time / times
        else:
            avg_run_time = "NA"

        print("")
        print(f"Average load time: {avg_load_time}")
        print(f"Average run time: {avg_run_time}")

        with open(FILENAME, 'a') as f:
            f.write(f"{name},{times},{avg_load_time},{avg_run_time}\n")


if __name__ == "__main__":
    FILENAME = get_result_filename()
    SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))
    bench()
