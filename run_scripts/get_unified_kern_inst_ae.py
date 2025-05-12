import os
import re
import pandas as pd
import numpy as np
import socket
import subprocess

DATA_FOLDER = '/data/EMT'
STAT_FOLDER = './inst_stats'
THP = 'never'

def extract_instructions_u(file_path):
    instructions_u = None
    pattern = re.compile(r"([\d,]+)\s+instructions:u")

    print("reading from ", file_path)
    with open(file_path, "r") as file:
        for line in file:
            match = pattern.search(line)
            if match:
                instructions_u = int(match.group(1).replace(",", ""))
                break  # Stop after the first match

    return instructions_u


def merge_inst_distributions(running_distro, loading_distro):
    running_df = pd.read_csv(
        running_distro, names=["symbol", "running_kern_inst"], header=None
    )
    running_df.set_index("symbol", inplace=True)

    loading_df = pd.read_csv(
        loading_distro, names=["symbol", "loading_kern_inst"], header=None
    )
    loading_df.set_index("symbol", inplace=True)

    merged = pd.concat([running_df, loading_df], axis=1)
    merged.fillna(0, inplace=True)
    merged.index = merged.index.to_series().fillna("syscall entry")

    return merged


def get_running_sim_inst(df, bench_data):

    running_sim = df["user_inst"][df.index == bench_data["workload"]].iloc[0]
    return running_sim


def get_loading_sim_inst(bench_data):
    if bench_data["workload"] == "sysbench":
        bench_data["sim_loading_inst"] = 376649127

    if bench_data["workload"] == "gups":
        bench_data["sim_loading_inst"] = 1718825887
    
    # if arch == "ecpt" and bench_data["test_name"] == "gups" and thp == "always":
    #     bench_data["sim_loading_inst"] = 1717900000
    
    return 2000000000

def produce_unified(bench_data):

    print(bench_data)
    running_inst = extract_instructions_u(bench_data["grd_running_inst"])
    loading_inst = extract_instructions_u(bench_data["grd_loading_inst"])

    TARGET_SIM_INST = 2000000000

    running_ratio = running_inst / (running_inst + loading_inst)
    loading_ratio = loading_inst / (running_inst + loading_inst)

    print(f"Running Ratio: {running_ratio}, Loading Ratio: {loading_ratio}")
    merged = merge_inst_distributions(
        bench_data["sim_running_distro"], bench_data["sim_loading_distro"]
    )

    print(merged)
    if "source_path" in merged.index:
        merged_no_source = merged.drop("source_path")
    else:
        merged_no_source = merged

    merged_no_source["running_kern_inst"] = merged_no_source[
        "running_kern_inst"
    ].astype(float)
    merged_no_source["loading_kern_inst"] = merged_no_source[
        "loading_kern_inst"
    ].astype(float)

    # syscall inst per user instruction
    merged_no_source["running_kern_inst_per_user_inst"] = (
        merged_no_source["running_kern_inst"] / bench_data["sim_running_inst"]
    )
    merged_no_source["loading_kern_inst_per_user_inst"] = (
        merged_no_source["loading_kern_inst"] / bench_data["sim_loading_inst"]
    )

    merged_no_source["unified_ratio"] = (
        merged_no_source["running_kern_inst_per_user_inst"] * running_ratio
        + merged_no_source["loading_kern_inst_per_user_inst"] * loading_ratio
    )

    merged_no_source["unified"] = merged_no_source["unified_ratio"] * TARGET_SIM_INST

    print(merged_no_source)
    unified_only = get_unified_only(merged_no_source, bench_data)

    running_loading_and_unified = pd.concat(
        [merged[["running_kern_inst", "loading_kern_inst"]], unified_only], axis=1
    )

    ratio_row = pd.DataFrame(
        {
            "running_kern_inst": [running_ratio],
            "loading_kern_inst": [loading_ratio],
            unified_only.columns[0]: [1],
        },
        index=["ratio"],
    )

    running_loading_and_unified = pd.concat([running_loading_and_unified, ratio_row])

    return unified_only, running_loading_and_unified


def read_sim_inst_csv(file_path):
    df = pd.read_csv(file_path, index_col=0)
    df = df.apply(pd.to_numeric, errors="ignore")
    return df


def get_unified_only(unified_df, bench_data):

    test_name = bench_data["workload"].replace("graphbig_", "")

    col = ""
    if bench_data["thp"] == "never":
        col = f'{test_name}_{bench_data["arch"]}_4KB_unified'
    elif bench_data["thp"] == "always":
        col = f'{test_name}_{bench_data["arch"]}_THP_unified'

    assert col != ""

    # unified_only = unified_df[['unified']]
    unified_df.rename(columns={"unified": col}, inplace=True)

    unified_only = unified_df[[col]]
    # running_loading_and_unified = unified_df[["running_kern_inst", "loading_kern_inst", col]]
    # print(final_unified_df)
    return unified_only


def rephrase_with_unified(unified_df, bench_data):

    test_name = bench_data["workload"].replace("graphbig_", "")

    col = ""
    if bench_data["thp"] == "never":
        col = f'{test_name}_{bench_data["arch"]}_4KB_unified'
    elif bench_data["thp"] == "always":
        col = f'{test_name}_{bench_data["arch"]}_THP_unified'

    assert col != ""

    # unified_only = unified_df[['unified']]
    unified_df.rename(columns={"unified": col}, inplace=True)

    unified_only = unified_df[[col]]
    running_loading_and_unified = unified_df[
        ["running_kern_inst", "loading_kern_inst", col]
    ]
    # print(final_unified_df)
    return unified_only, running_loading_and_unified


def popuate_from_datapath(data_path_df, bench_data):
    if ('fpt' in bench_data["arch"]):
        return
    is_workload = data_path_df["workload"] == bench_data["workload"]
    is_arch = data_path_df["arch"] == bench_data["arch"]
    is_thp = data_path_df["thp"] == bench_data["thp"]

    sub_df = data_path_df[is_workload & is_arch & is_thp]

    running_path = os.path.join(
        sub_df[sub_df["stage"] == "running"]["folder"].iloc[0],
        sub_df[sub_df["stage"] == "running"]["path"].iloc[0],
    )
    loading_path = os.path.join(
        sub_df[sub_df["stage"] == "loading"]["folder"].iloc[0],
        sub_df[sub_df["stage"] == "loading"]["path"].iloc[0],
    )

    print(running_path)
    print(loading_path)
    bench_data["sim_running_distro"] = os.path.abspath(running_path)
    bench_data["sim_loading_distro"] = os.path.abspath(loading_path)

def scp_from_remote(host, remote_path, local_path):
    """
    Transfers a file from a remote machine to the local machine using SCP via subprocess.
    """
    try:
        # Construct the SCP command
        scp_command = ["scp", f"{host}:{remote_path}", local_path]
        # if key_file:
        #     scp_command.extend(["-i", key_file])
        # scp_command.append(f"{username}@{host}:{remote_path}")
        # scp_command.append(local_path)

        # Execute the command
        subprocess.run(scp_command, check=True)
        print(f"File successfully copied from {host}:{remote_path} to {local_path}")
    except subprocess.CalledProcessError as e:
        print(f"An error occurred while running SCP: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

def fetch_bench_files(machine, path, local_dir="local"):
    hostname = socket.gethostname()
    os.makedirs(local_dir, exist_ok=True)

    if machine == hostname:
        filename = path
    else:
        filename = f"local/{os.path.basename(path)}.local"
        os.makedirs("local", exist_ok=True)
        scp_from_remote(machine, path, filename)

    return filename

def populate_FPT_sim_path_L2L3(bench_data, thp):
    # sub_folder = "fpt_os/fpt_L3L2"
    
    # flavor = "L3L2"
    # stage = "running"
    # running_path = {
    #     "graphbig_bfs": f'{sub_folder}/fpt_{thp}_graphbig_bfs_{stage}_walk_log.bin.kern_inst.folded.high_level.csv',
    #     "graphbig_dfs": f'{sub_folder}/fpt_{thp}_graphbig_dfs_{stage}_walk_log.bin.kern_inst.folded.high_level.csv',
    #     "graphbig_dc": f'{sub_folder}/fpt_{thp}_graphbig_dc_{stage}_walk_log.bin.kern_inst.folded.high_level.csv',
    #     "graphbig_sssp": f'{sub_folder}/fpt_{thp}_graphbig_sssp_{stage}_walk_log.bin.kern_inst.folded.high_level.csv',
    #     "graphbig_cc": f'{sub_folder}/fpt_{thp}_graphbig_cc_{stage}_walk_log.bin.kern_inst.folded.high_level.csv',
    #     "graphbig_tc": f'{sub_folder}/fpt_{thp}_graphbig_tc_{stage}_walk_log.bin.kern_inst.folded.high_level.csv',
    #     "graphbig_pagerank": f'{sub_folder}/fpt_{thp}_graphbig_pagerank_{stage}_walk_log.bin.kern_inst.folded.high_level.csv',
    #     "sysbench": f'{sub_folder}/fpt_{thp}_sysbench_{stage}_walk_log.bin.kern_inst.folded.high_level.csv',
    #     "gups": f'{sub_folder}/fpt_{thp}_gups_{stage}_walk_log.bin.kern_inst.folded.high_level.csv',
    #     "redis": f'{sub_folder}/fpt_L3L2_never_{stage}_jiyuan_redis_run_128G.bin.kern_inst.folded.high_level.csv',
    #     "memcached": f'{sub_folder}/fpt_{flavor}_{thp}_memcached_{stage}_walk_log.bin.kern_inst.folded.high_level.csv',
    #     "postgres": f'{sub_folder}/fpt_L3L2_never_run_postgres64G_sequential_load_{stage}.bin.kern_inst.folded.high_level.csv',
    # }
    
    # stage = "loading_end_phase"
    # loading_end_path = {
    #     "graphbig_bfs": f'{sub_folder}/fpt_{thp}_graphbig_bfs_{stage}_walk_log.bin.kern_inst.folded.high_level.csv',
    #     "graphbig_dfs": f'{sub_folder}/fpt_{thp}_graphbig_dfs_{stage}_walk_log.bin.kern_inst.folded.high_level.csv',
    #     "graphbig_dc": f'{sub_folder}/fpt_{thp}_graphbig_dc_{stage}_walk_log.bin.kern_inst.folded.high_level.csv',
    #     "graphbig_sssp": f'{sub_folder}/fpt_{thp}_graphbig_sssp_{stage}_walk_log.bin.kern_inst.folded.high_level.csv',
    #     "graphbig_cc": f'{sub_folder}/fpt_{thp}_graphbig_cc_{stage}_walk_log.bin.kern_inst.folded.high_level.csv',
    #     "graphbig_tc": f'{sub_folder}/fpt_{thp}_graphbig_tc_{stage}_walk_log.bin.kern_inst.folded.high_level.csv',
    #     "graphbig_pagerank": f'{sub_folder}/fpt_{thp}_graphbig_pagerank_{stage}_walk_log.bin.kern_inst.folded.high_level.csv',
    #     "sysbench": f'{sub_folder}/fpt_{flavor}_{thp}_sysbench_{stage}_walk_log.bin.kern_inst.folded.high_level.csv',
    #     "gups": f'{sub_folder}/fpt_{flavor}_{thp}_gups_{stage}_walk_log.bin.kern_inst.folded.high_level.csv',
    #     "redis": f'{sub_folder}/fpt_L3L2_never_{stage}_jiyuan_redis_run_128G.bin.kern_inst.folded.high_level.csv',
    #     "memcached": f'{sub_folder}/fpt_{flavor}_{thp}_memcached_{stage}_walk_log.bin.kern_inst.folded.high_level.csv',
    #     "postgres": f'{sub_folder}/fpt_L3L2_never_run_postgres64G_sequential_load_loading_end.bin.kern_inst.folded.high_level.csv',
    # }

    running_folder = '/data1/fpt_report/fpt_L3L2/running'
    
    benchs = [
        'graphbig_bfs',
        'graphbig_dfs',
        'graphbig_dc',
        'graphbig_sssp',
        'graphbig_cc',
        'graphbig_tc',
        'graphbig_pagerank',
        'sysbench',
        'gups',
    ]
    running_bench_infos = [(b,              'frontier', f'{running_folder}/fpt_L3L2_never_{b}_running_walk_log.bin.kern_inst.folded.high_level.csv') for b in benchs]
    running_bench_infos += [('redis',        'CSL',      '/disk/bak1/siyuan/fpt_L3L2/running_phase/fpt_L3L2_never_running_jiyuan_redis_run_128G.bin.kern_inst.folded.high_level.csv')]
    running_bench_infos += [('memcached',    'frontier', '/data1/fpt_report/Memcached64Gpure_20insertion/fpt_L3L2_never_run_Memcached64Gpure_20insertion_running.bin.kern_inst.folded.high_level.csv')]
    running_bench_infos += [('postgres',     'CSL',      '/disk/bak1/siyuan/fpt_L3L2/running_phase/fpt_L3L2_never_run_postgres64G_sequential_load_running.bin.kern_inst.folded.high_level.csv')]

    for b, machine, path in running_bench_infos:
        if b == bench_data["workload"]:
            break
    running_path = fetch_bench_files(machine, path, local_dir="local")

    loading_end_folder = '/data1/fpt_report/fpt_L3L2/loading_end_phase'
    
    loading_end_bench_infos = [(b,              'frontier', f'{loading_end_folder}/fpt_L3L2_never_{b}_loading_end_phase_walk_log.bin.kern_inst.folded.high_level.csv') for b in benchs]
    loading_end_bench_infos += [('redis',        'CSL',      '/disk/bak1/siyuan/fpt_L3L2/loading_end_phase/fpt_L3L2_never_loading_end_phase_jiyuan_redis_run_128G.bin.kern_inst.folded.high_level.csv')]
    loading_end_bench_infos += [('memcached',    'frontier', '/data1/fpt_report/Memcached64Gpure_20insertion/fpt_L3L2_never_run_Memcached64Gpure_20insertion_loading_end.bin.kern_inst.folded.high_level.csv')]
    loading_end_bench_infos += [('postgres',     'CSL',      '/disk/bak1/siyuan/fpt_L3L2/loading_end_phase/fpt_L3L2_never_run_postgres64G_sequential_load_loading_end.bin.kern_inst.folded.high_level.csv')]

    for b, machine, path in loading_end_bench_infos:
        if b == bench_data["workload"]:
            break
    loading_end_path = fetch_bench_files(machine, path, local_dir="local")
    
    bench_data["sim_running_distro"] = running_path
    bench_data["sim_loading_distro"] = loading_end_path

def populate_FPT_sim_path_L4L3_L2L1(bench_data, thp):
    # sub_folder = "fpt_os/fpt_L4L3_L2L1"
    
    # flavor = "L4L3_L2L1"
    # stage = "running"
    
    # running_path = {
    #     "graphbig_bfs": f'{sub_folder}/fpt_{thp}_graphbig_bfs_{stage}_walk_log.bin.kern_inst.folded.high_level.csv',
    #     "graphbig_dfs": f'{sub_folder}/fpt_{thp}_graphbig_dfs_{stage}_walk_log.bin.kern_inst.folded.high_level.csv',
    #     "graphbig_dc": f'{sub_folder}/fpt_{thp}_graphbig_dc_{stage}_walk_log.bin.kern_inst.folded.high_level.csv',
    #     "graphbig_sssp": f'{sub_folder}/fpt_{thp}_graphbig_sssp_{stage}_walk_log.bin.kern_inst.folded.high_level.csv',
    #     "graphbig_cc": f'{sub_folder}/fpt_{thp}_graphbig_cc_{stage}_walk_log.bin.kern_inst.folded.high_level.csv',
    #     "graphbig_tc": f'{sub_folder}/fpt_{thp}_graphbig_tc_{stage}_walk_log.bin.kern_inst.folded.high_level.csv',
    #     "graphbig_pagerank": f'{sub_folder}/fpt_{thp}_graphbig_pagerank_{stage}_walk_log.bin.kern_inst.folded.high_level.csv',
    #     "sysbench": f'{sub_folder}/fpt_{flavor}_{thp}_sysbench_{stage}_walk_log.bin.kern_inst.folded.high_level.csv',
    #     "gups": f'{sub_folder}/fpt_{flavor}_{thp}_gups_{stage}_walk_log.bin.kern_inst.folded.high_level.csv',
    #     "redis": f'{sub_folder}/fpt_L4L3_L2L1_never_{stage}_jiyuan_redis_run_128G.bin.kern_inst.folded.high_level.csv',
    #     "memcached": f'{sub_folder}/fpt_L4L3_L2L1_never_run_Memcached64Gpure_20insertion_running.bin.kern_inst.folded.high_level.csv',
    #     "postgres": f'{sub_folder}/fpt_L4L3_L2L1_never_run_postgres64G_sequential_load_running.bin.kern_inst.folded.high_level.csv',
    # }
    
    # stage = "loading_end_phase"
    # loading_end_path = {
    #     "graphbig_bfs": f'{sub_folder}/fpt_{flavor}_{thp}_graphbig_bfs_{stage}_walk_log.bin.kern_inst.folded.high_level.csv',
    #     "graphbig_dfs": f'{sub_folder}/fpt_{flavor}_{thp}_graphbig_dfs_{stage}_walk_log.bin.kern_inst.folded.high_level.csv',
    #     "graphbig_dc": f'{sub_folder}/fpt_{flavor}_{thp}_graphbig_dc_{stage}_walk_log.bin.kern_inst.folded.high_level.csv',
    #     "graphbig_sssp": f'{sub_folder}/fpt_{flavor}_{thp}_graphbig_sssp_{stage}_walk_log.bin.kern_inst.folded.high_level.csv',
    #     "graphbig_cc": f'{sub_folder}/fpt_{flavor}_{thp}_graphbig_cc_{stage}_walk_log.bin.kern_inst.folded.high_level.csv',
    #     "graphbig_tc": f'{sub_folder}/fpt_{flavor}_{thp}_graphbig_tc_{stage}_walk_log.bin.kern_inst.folded.high_level.csv',
    #     "graphbig_pagerank": f'{sub_folder}/fpt_{flavor}_{thp}_graphbig_pagerank_{stage}_walk_log.bin.kern_inst.folded.high_level.csv',
    #     "sysbench": f'{sub_folder}/fpt_{flavor}_{thp}_sysbench_{stage}_walk_log.bin.kern_inst.folded.high_level.csv',
    #     "gups": f'{sub_folder}/fpt_{flavor}_{thp}_gups_{stage}_walk_log.bin.kern_inst.folded.high_level.csv',
    #     "redis": f'{sub_folder}/fpt_L4L3_L2L1_never_loading_end_phase_jiyuan_redis_run_128G.bin.kern_inst.folded.high_level.csv',
    #     "memcached": f'{sub_folder}/fpt_L4L3_L2L1_never_run_Memcached64Gpure_20insertion_loading_end.bin.kern_inst.folded.high_level.csv',
    #     "postgres": f'{sub_folder}/fpt_L4L3_L2L1_never_run_postgres64G_sequential_load_loading_end.bin.kern_inst.folded.high_level.csv',
    # }
    
    running_folder = '/data1/fpt_report/fpt_L4L3_L2L1/running'
    
    benchs = [
        'graphbig_bfs',
        'graphbig_dfs',
        'graphbig_dc',
        'graphbig_sssp',
        'graphbig_cc',
        'graphbig_tc',
        'graphbig_pagerank',
        'sysbench',
        'gups',
    ]
    running_bench_infos = [(b,              'frontier', f'{running_folder}/fpt_L4L3_L2L1_never_{b}_running_walk_log.bin.kern_inst.folded.high_level.csv') for b in benchs]
    running_bench_infos += [('redis',        'CSL',      '/disk/bak1/siyuan/fpt_L4L3_L2L1/running_phase/fpt_L4L3_L2L1_never_running_redis_run_128G.bin.kern_inst.folded.high_level.csv')]
    running_bench_infos += [('memcached',    'frontier', '/data1/fpt_report/Memcached64Gpure_20insertion/fpt_L4L3_L2L1_never_run_Memcached64Gpure_20insertion_running.bin.kern_inst.folded.high_level.csv')]
    running_bench_infos += [('postgres',     'CSL',      '/disk/bak1/siyuan/fpt_L4L3_L2L1/running_phase/fpt_L4L3_L2L1_never_run_postgres64G_sequential_load_running.bin.kern_inst.folded.high_level.csv')]

    for b, machine, path in running_bench_infos:
        if b == bench_data["workload"]:
            break
    running_path = fetch_bench_files(machine, path, local_dir="local")

    loading_end_folder = '/data2/fpt_kexec_temp/fpt_L4L3_L2L1/loading_end_phase'
    
    loading_end_bench_infos = [(b,              'ajisai', f'{loading_end_folder}/fpt_L4L3_L2L1_never_{b}_loading_end_phase_walk_log.bin.kern_inst.folded.high_level.csv') for b in benchs]
    loading_end_bench_infos += [('redis',        'CSL',      '/disk/bak1/siyuan/fpt_L4L3_L2L1/loading_end_phase/fpt_L4L3_L2L1_never_loading_end_phase_redis_run_128G.bin.kern_inst.folded.high_level.csv')]
    loading_end_bench_infos += [('memcached',    'ajisai', '/data2/fpt_kexec_temp/Memcached64Gpure_20insertion/fpt_L4L3_L2L1_never_run_Memcached64Gpure_20insertion_loading_end.bin.kern_inst.folded.high_level.csv')]
    loading_end_bench_infos += [('postgres',     'CSL',      '/disk/bak1/siyuan/fpt_L4L3_L2L1/loading_end_phase/fpt_L4L3_L2L1_never_run_postgres64G_sequential_load_loading_end.bin.kern_inst.folded.high_level.csv')]

    for b, machine, path in loading_end_bench_infos:
        if b == bench_data["workload"]:
            break
    loading_end_path = fetch_bench_files(machine, path, local_dir="local")
    
    
    bench_data["sim_running_distro"] = os.path.abspath(running_path)
    bench_data["sim_loading_distro"] = os.path.abspath(loading_end_path)
    

def get_result_per_kernel_thp_test(arch, thp, test_name, sim_inst_df):

    sim_running_distro_folder = "kernel_inst"
    sim_loading_distro_folder = "kernel_inst_high_level"

    csv_file_suffix = ".high_level.csv"
    intermediate = ""
    if thp == "always":
        # wrong ecpt thp data
        intermediate = "_insn_None"
        sim_loading_distro_folder = "kernel_inst_loading/full_kernel_withIter_withPlace"
        csv_file_suffix = ".reprocessed.high_level.csv"

    bench_data = {
        "workload": test_name,
        "arch": arch,
        "thp": thp,
        "grd_running_inst": os.path.abspath(
            f"inst_perf/{test_name}_running_inst_perf.txt"
        ),
        "grd_loading_inst": os.path.abspath(
            f"inst_perf/{test_name}_loading_inst_perf.txt"
        ),
        "sim_running_distro": os.path.abspath(
            f"{sim_running_distro_folder}/{arch}_{thp}_{test_name}_walk_log.bin{intermediate}.kern_inst.folded{csv_file_suffix}"
        ),
        "sim_loading_distro": os.path.abspath(
            f"{sim_loading_distro_folder}/{arch}_{thp}_{test_name}_walk_log.bin.kern_inst.folded{csv_file_suffix}"
        ),
    }

    if test_name == "sysbench":
        bench_data["grd_running_inst"] = os.path.abspath(
            f"inst_perf/{test_name}_total_running_inst_perf.txt"
        )
        bench_data["grd_loading_inst"] = os.path.abspath(
            f"inst_perf/{test_name}_total_loading_inst_perf.txt"
        )

    if test_name == "sysbench" and thp == "always":
        bench_data["sim_running_distro"] = os.path.abspath(
            f"{sim_running_distro_folder}/{arch}_{thp}_{test_name}_running_walk_log.bin.kern_inst.folded{csv_file_suffix}"
        )

    data_path_df = pd.read_csv("run_scripts/unified_data_path.csv")
    if test_name == "redis":
        popuate_from_datapath(data_path_df, bench_data)
    elif test_name == "memcached":
        popuate_from_datapath(data_path_df, bench_data)
    elif test_name == "postgres":
        popuate_from_datapath(data_path_df, bench_data)
        # test_code_name = "run_postgres64G_sequential_load"
        # test_code_name = 'run_postgres64G_two_different_seed_64_shared_mem_40M_entries'
        test_code_name_real_inst = "postgres_seqeuntial_21M"
        bench_data["grd_running_inst"] = os.path.abspath(
            f"inst_perf/{test_code_name_real_inst}_running_inst_perf.txt"
        )
        bench_data["grd_loading_inst"] = os.path.abspath(
            f"inst_perf/{test_code_name_real_inst}_loading_inst_perf.txt"
        )

    # if arch == 'fpt':
    #     populate_FPT_sim_path(bench_data)

    bench_data["sim_running_inst"] = get_running_sim_inst(
        sim_inst_df, bench_data
    )  # Get running simulation instructions
    bench_data["sim_loading_inst"] = get_loading_sim_inst(
        bench_data
    )  # Get loading simulation instructions

    unified_only, running_loading_and_unified = produce_unified(
        bench_data
    )  # Call the function to produce unified instructions
    # unified_only, running_loading_and_unified  = rephrase_with_unified(df, bench_data)

    return unified_only, running_loading_and_unified


def get_result_per_kernel_thp_test_loading_end(arch, thp, test_name, sim_inst_df):

    sim_running_distro_folder = f"{DATA_FOLDER}/{arch}/running"
    sim_loading_distro_folder = f"{DATA_FOLDER}/{arch}/loading_end"

    csv_file_suffix = ".high_level.csv"
    intermediate = ""
    if thp == "always":
        # wrong ecpt thp data
        # intermediate = "_insn_None"
        # sim_loading_distro_folder = "kernel_inst_loading/full_kernel_withIter_withPlace"
        csv_file_suffix = ".reprocessed.high_level.csv"

    bench_data = {
        "workload": test_name,
        "arch": arch,
        "thp": thp,
        "grd_running_inst": os.path.abspath(
            f"inst_perf/{test_name}_running_inst_perf.txt"
        ),
        "grd_loading_inst": os.path.abspath(
            f"inst_perf/{test_name}_loading_inst_perf.txt"
        ),
        "sim_running_distro": os.path.abspath(
            f"{sim_running_distro_folder}/{arch}_{thp}_{test_name}_running_walk_log.bin{intermediate}.kern_inst.folded{csv_file_suffix}"
        ),
        "sim_loading_distro": os.path.abspath(
            f"{sim_loading_distro_folder}/{arch}_{thp}_{test_name}_loading_end_walk_log.bin.kern_inst.folded{csv_file_suffix}"
        ),
    }

    if test_name == "sysbench":
        bench_data["grd_running_inst"] = os.path.abspath(
            f"inst_perf/{test_name}_total_running_inst_perf.txt"
        )
        bench_data["grd_loading_inst"] = os.path.abspath(
            f"inst_perf/{test_name}_total_loading_inst_perf.txt"
        )

    if test_name == "sysbench" and thp == "always":
        bench_data["sim_running_distro"] = os.path.abspath(
            f"{sim_running_distro_folder}/{arch}_{thp}_{test_name}_running_walk_log.bin.kern_inst.folded{csv_file_suffix}"
        )

    data_path_df = pd.read_csv("run_scripts/unified_data_path_loading_end.csv")
    
    
    
    if test_name == "redis":
        popuate_from_datapath(data_path_df, bench_data)
    elif test_name == "memcached":
        popuate_from_datapath(data_path_df, bench_data)
    elif test_name == "postgres":
        popuate_from_datapath(data_path_df, bench_data)
        # test_code_name = "run_postgres64G_sequential_load"
        # test_code_name = 'run_postgres64G_two_different_seed_64_shared_mem_40M_entries'
        test_code_name_real_inst = "postgres_seqeuntial_21M"
        bench_data["grd_running_inst"] = os.path.abspath(
            f"inst_perf/{test_code_name_real_inst}_running_inst_perf.txt"
        )
        bench_data["grd_loading_inst"] = os.path.abspath(
            f"inst_perf/{test_code_name_real_inst}_loading_inst_perf.txt"
        )

    bench_data["sim_running_inst"] = get_running_sim_inst(
        sim_inst_df, bench_data
    )  # Get running simulation instructions
    bench_data["sim_loading_inst"] = get_loading_sim_inst(
        bench_data
    )  # Get loading simulation instructions

    # if test_name == "sysbench":
    #     bench_data["sim_loading_inst"] = 376649127

    # if arch == "ecpt" and test_name == "gups" and thp == "always":
    #     bench_data["sim_loading_inst"] = 1717900000

    if arch == 'fpt_L3L2':
        populate_FPT_sim_path_L2L3(bench_data, thp)
    elif arch == 'fpt_L4L3_L2L1':
        populate_FPT_sim_path_L4L3_L2L1(bench_data, thp)

    unified_only, running_loading_and_unified = produce_unified(
        bench_data
    )  # Call the function to produce unified instructions
    # unified_only, running_loading_and_unified  = rephrase_with_unified(df, bench_data)

    return unified_only, running_loading_and_unified

def reprocess_with_category(percent_df):

    df = percent_df.copy()

    df.rename(
        index={
            "asm_exc_page_fault": "Page Faults",
            "asm_sysvec_apic_timer_interrupt": "__Timers",
            'irq_entries_start' : "__Timers",
        },
        inplace=True,
    )

    sys_index = df.index.str.contains("sys") | df.index.str.contains("SYS")
    system_calls_sum = df[sys_index].sum()
    df = df[~sys_index]

    df.loc["System Calls"] = system_calls_sum

    timer_idx = df.index.str.contains('__Timers')
    timer_sum = df[timer_idx].sum()
    df = df[~timer_idx]

    df.loc["Timers"] = timer_sum

    df.fillna(0, inplace=True)

    if "khugepaged" not in df.index:
        df.loc["khugepaged"] = 0
    df.rename(
        index={
            "asm_exc_page_fault": "Page Faults",
            "asm_sysvec_apic_timer_interrupt": "Timers",
            "others": "Others",
            "khugepaged": "khugepaged (THP)",
        },
        inplace=True,
    )

    return df


def merge_per_thp_per_test(per_thp_test_dfs, key):
    merged = pd.DataFrame()
    for df in per_thp_test_dfs:
        # if 'irq_entries_start' in df.index:
        #     df = df.drop('irq_entries_start')
        merged = pd.concat([merged, df], axis=1)
    merged.fillna(0, inplace=True)

    # get relative base
    base_sum = merged[key].sum()
    relative = merged / base_sum

    small_idx = relative < 0.009

    percent_cleaned = relative[~small_idx].dropna(how="all")
    # append those small entries to the last entry
    other_sums = relative[small_idx].sum(axis=0).rename("others")
    percent_cleaned = percent_cleaned._append(other_sums)

    percent_cleaned.index = np.array(
        [element.lstrip("__") for element in percent_cleaned.index]
    )

    print(percent_cleaned)
    # print(merged)

    return percent_cleaned
    # return percent_cleaned, merged, atlair_reprocessed


def move_row_to_end(df, index_key):
    if index_key not in df.index:
        return df

    row_to_move = df.loc[[index_key]]
    df = df.drop(index_key)

    # Append the row at the end of the DataFrame
    df = pd.concat([df, row_to_move])
    return df


def all_merge(raws_alltests, thp):
    merged = pd.DataFrame()
    for df in raws_alltests:
        merged = pd.concat([merged, df], axis=1)
    merged.fillna(0, inplace=True)

    merged = move_row_to_end(merged, "ratio")
    merged = move_row_to_end(merged, "source_path")

    path = f"{STAT_FOLDER}/merged_unified_raw_{thp}_{loading_phase}.csv"
    
    merged.to_csv(path)

    print("raw result saved to", path)


def get_user_instructions(tests):

    data_list = []

    for test in tests:

        if test == "sysbench":
            test_real_name = "sysbench_total"
        elif test == "postgres":
            test_real_name = "postgres_seqeuntial_21M"
        else:
            test_real_name = test

        bench_data = {
            "workload": test,
            "grd_running_inst_path": os.path.abspath(
                f"inst_perf/{test_real_name}_running_inst_perf.txt"
            ),
            "grd_loading_inst_path": os.path.abspath(
                f"inst_perf/{test_real_name}_loading_inst_perf.txt"
            ),
        }

        bench_data["grd_running_inst"] = extract_instructions_u(
            bench_data["grd_running_inst_path"]
        )
        bench_data["grd_loading_inst"] = extract_instructions_u(
            bench_data["grd_loading_inst_path"]
        )

        bench_data["running_ratio"] = bench_data["grd_running_inst"] / (
            bench_data["grd_running_inst"] + bench_data["grd_loading_inst"]
        )
        bench_data["loading_ratio"] = bench_data["grd_loading_inst"] / (
            bench_data["grd_running_inst"] + bench_data["grd_loading_inst"]
        )

        data_list = data_list + [bench_data]

    u_inst_df = pd.DataFrame(data_list)
    u_inst_df.set_index("workload", inplace=True)
    u_inst_df.to_csv("grd_inst.csv")

    print("save to ", "grd_inst.csv")
    return u_inst_df


def transform_to_atlair(all_tests, group_factor, thp):

    merged = pd.DataFrame()
    for df in all_tests:
        altlair_form_df = reprocess_with_category(df)
        merged = pd.concat([merged, altlair_form_df], axis=1)
    merged.fillna(0, inplace=True)

    print(merged)
    merged.to_csv(f"{STAT_FOLDER}/merged_relative_{thp}_{loading_phase}.csv")
    print("relative result saved to ", f"{STAT_FOLDER}/merged_relative_{thp}_{loading_phase}.csv")
  
    df_melted = merged.reset_index().melt(id_vars="index")

    df_melted["system"] = df_melted["variable"].apply(
        lambda x: "x86" if "radix" in x else "ECPT"
    )
    df_melted["workload"] = df_melted["variable"].apply(
        lambda x: x.split("_")[0].upper()
    )

    df_melted["workload"] = df_melted["workload"].replace(
        {
            "PAGERANK": "PR",
            "SYSBENCH": "Sysbench",
            "REDIS": "Redis",
            "MEMCACHED": "Memcached",
            "POSTGRES": "Postgres",
        }
    )

    df_melted.rename(
        columns={"index": "function", "value": "instruction"}, inplace=True
    )
    transformed_df = df_melted[["workload", "system", "instruction", "function"]]

    print(transformed_df)

    transformed_df.to_csv(f"{STAT_FOLDER}/kern_inst_{THP}_unified.csv", index=False)



if __name__ == "__main__":

    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--input')
    parser.add_argument('--output')
    parser.add_argument('--thp')
    args = parser.parse_args()

    if args.input:
        DATA_FOLDER = args.input
    if args.output:
        STAT_FOLDER = args.output
    if args.thp:
        THP = args.thp
    if THP != "always" and THP != "never":
        raise ValueError("THP should be 'always' or 'never'")

    if not os.path.exists(STAT_FOLDER):
        os.makedirs(STAT_FOLDER, exist_ok=True)

    loading_phase = "end"
    sim_inst_df = read_sim_inst_csv("run_scripts/sim_inst.csv")

    archs = [
        "radix",
        "ecpt",
        # 'fpt_L3L2',
        # 'fpt_L4L3_L2L1'
    ]

    # THP_options = [
    #     "never",
    #     # "always",
    # ]

    tests = [
        "graphbig_bfs",
        # "graphbig_dfs",
        # "graphbig_dc",
        # "graphbig_sssp",
        # "graphbig_cc",
        # "graphbig_tc",
        # "graphbig_pagerank",
        # "sysbench",
        "gups",
        "redis",
        # "memcached",
        # "postgres",
    ]

    get_user_instructions(tests)

    # for thp in THP_options:
    all_tests_percents = []
    raws = []
    atlair_dfs = []
    for test in tests:
        per_test = []
        for kernel in archs:
            df, running_loading_and_unified = get_result_per_kernel_thp_test_loading_end(
                kernel, THP, test, sim_inst_df
            )
            per_test.append(df)
            raws.append(running_loading_and_unified)

        percent_df = merge_per_thp_per_test(per_test, per_test[0].columns[0])
        all_tests_percents.append(percent_df)

    all_merge(raws, THP)

    transform_to_atlair(all_tests_percents, group_factor=len(archs), thp=THP)
