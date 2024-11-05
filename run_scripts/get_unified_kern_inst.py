import os
import re
import pandas as pd
import numpy as np

def extract_instructions_u(file_path):
    instructions_u = None
    pattern = re.compile(r'([\d,]+)\s+instructions:u')
    
    print("reading from ", file_path)
    with open(file_path, 'r') as file:
        for line in file:
            match = pattern.search(line)
            if match:
                instructions_u = int(match.group(1).replace(",", ""))
                break  # Stop after the first match
    
    return instructions_u

def merge_inst_distributions(running_distro, loading_distro): 
    running_df = pd.read_csv(running_distro, names=['symbol', 'running_kern_inst'], header=None)
    running_df.set_index('symbol', inplace=True)
    
    loading_df = pd.read_csv(loading_distro, names=['symbol', 'loading_kern_inst'], header=None)
    loading_df.set_index('symbol', inplace=True)
    
    merged = pd.concat([running_df, loading_df], axis=1)
    merged.fillna(0,inplace=True)
    merged.index = merged.index.to_series().fillna('syscall entry')

    return merged

def get_running_sim_inst(df, bench_data):
 
    running_sim = df["user_inst"][df.index == bench_data['workload']].iloc[0]
    return running_sim
    
    
def get_loading_sim_inst(bench_data):
    return 2000000000

def produce_unified(bench_data):

    print(bench_data)
    running_inst = extract_instructions_u(bench_data["grd_running_inst"])
    loading_inst = extract_instructions_u(bench_data["grd_loading_inst"])
    
    
    TARGET_SIM_INST = 2000000000
    
    running_ratio = running_inst / (running_inst + loading_inst)
    loading_ratio = loading_inst / (running_inst + loading_inst)
    
    print(f'Running Ratio: {running_ratio}, Loading Ratio: {loading_ratio}')
    merged = merge_inst_distributions(
            bench_data["sim_running_distro"], 
            bench_data["sim_loading_distro"])
    
    # syscall inst per user instruction
    merged["running_kern_inst_per_user_inst"] = merged["running_kern_inst"] / bench_data["sim_running_inst"] 
    merged["loading_kern_inst_per_user_inst"] = merged["loading_kern_inst"] / bench_data["sim_loading_inst"] 
    
    merged["unified_ratio"] = (merged["running_kern_inst_per_user_inst"] * running_ratio + merged["loading_kern_inst_per_user_inst"] * loading_ratio)
    
    merged["unified"] = merged["unified_ratio"] *TARGET_SIM_INST
    
    print(merged)
    return merged

def read_sim_inst_csv(file_path):
    df = pd.read_csv(file_path, index_col=0)
    df = df.apply(pd.to_numeric, errors='ignore')
    return df

def rephrase_with_unified(unified_df, bench_data):
    
    test_name = bench_data["workload"].replace('graphbig_', '')
    
    col = ''
    if bench_data["thp"] == "never":
        col = f'{test_name}_{bench_data["arch"]}_4KB_unified'
    elif bench_data["thp"] == "always":
        col = f'{test_name}_{bench_data["arch"]}_THP_unified'

    assert col != ''
    
    # unified_only = unified_df[['unified']]
    unified_df.rename(columns={'unified': col}, inplace=True)
    
    unified_only = unified_df[[col]]
    running_loading_and_unified = unified_df[["running_kern_inst", "loading_kern_inst", col]]
    # print(final_unified_df)
    return unified_only, running_loading_and_unified
    

def get_result_per_kernel_thp_test(arch, thp, test_name, sim_inst_df):
    bench_data = {
        "workload" : test_name,
        "arch": arch,
        "thp" : thp,
        "grd_running_inst" : os.path.abspath(f"inst_perf/{test_name}_running_inst_perf.txt"),
        "grd_loading_inst" : os.path.abspath(f"inst_perf/{test_name}_loading_inst_perf.txt"),
        
        "sim_running_distro" : os.path.abspath(f"kernel_inst/{arch}_{thp}_{test_name}_walk_log.bin.kern_inst.folded.high_level.csv"),
        "sim_loading_distro" : os.path.abspath(f"kernel_inst_high_level/{arch}_{thp}_{test_name}_walk_log.bin.kern_inst.folded.high_level.csv"),
    }

    if test_name == 'redis':
        test_code_name = 'jiyuan_redis_run_128G'
        bench_data["sim_running_distro"] = os.path.abspath(f"kernel_inst/{arch}_{thp}_{test_code_name}.bin.kern_inst.folded.high_level.csv")
        bench_data["sim_loading_distro"] = os.path.abspath(f"kernel_inst_high_level/{arch}_{thp}_run_{test_code_name}_kexec_loading_first_2B.bin.kern_inst.folded.high_level.csv")
        
        if arch == 'ecpt':
            # bench_data["sim_running_distro"] = os.path.abspath(f"kernel_inst/{arch}_{thp}_ecpt_never_run_{test_code_name}.bin.kern_inst.folded.high_level.csv")
            bench_data["sim_loading_distro"] = '/hdd/alan_loading_phase/jiyuan_redis_run_128G_rerun/ecpt_never_run_jiyuan_redis_run_128G_rerun_loading.bin.kern_inst.folded.high_level.csv'
        
        # ecpt_never_run_jiyuan_redis_run_128G_kexec_loading_first_2B.bin.kern_inst.folded.high_level.csv
    elif test_name == 'memcached': 
        test_code_name = 'run_Memcached64Gpure_20insertion_never'
        bench_data["sim_running_distro"] = os.path.abspath(f"kernel_inst/{arch}_{thp}_{test_code_name}.bin.kern_inst.folded.high_level.csv")
        bench_data["sim_loading_distro"] = os.path.abspath(f"kernel_inst_high_level/{arch}_{thp}_{test_code_name}_kexec_loading_first_2B.bin.kern_inst.folded.high_level.csv")
    elif test_name == 'postgres':
        test_code_name = 'run_postgres64G_sequential_load'
        # test_code_name = 'run_postgres64G_two_different_seed_64_shared_mem_40M_entries'
        test_code_name_real_inst = 'postgres_seqeuntial_21M'
        bench_data['grd_running_inst'] = os.path.abspath(f"inst_perf/{test_code_name_real_inst}_running_inst_perf.txt")
        bench_data['grd_loading_inst'] = os.path.abspath(f"inst_perf/{test_code_name_real_inst}_loading_inst_perf.txt")
        
        bench_data["sim_running_distro"] = os.path.abspath(f"kernel_inst/{arch}_{thp}_{test_code_name}.bin.kern_inst.folded.high_level.csv")
        # bench_data["sim_loading_distro"] = os.path.abspath(f"kernel_inst_high_level/{arch}_{thp}_{test_code_name}_kexec_loading_first_2B.bin.kern_inst.folded.high_level.csv")
        bench_data["sim_loading_distro"] = os.path.abspath(f"kernel_inst_high_level/{arch}_{thp}_{test_code_name}_loading.bin.kern_inst.folded.high_level.csv")
        
    bench_data["sim_running_inst"] = get_running_sim_inst(sim_inst_df, bench_data)  # Get running simulation instructions
    bench_data["sim_loading_inst"] = get_loading_sim_inst(bench_data)  # Get loading simulation instructions

    df = produce_unified(bench_data)  # Call the function to produce unified instructions
    unified_only, running_loading_and_unified  = rephrase_with_unified(df, bench_data)
    
    return unified_only, running_loading_and_unified

def reprocess_with_category(percent_df):

    df = percent_df.copy()

    df.rename(index={
        "asm_exc_page_fault": "Page Faults",
        "asm_sysvec_apic_timer_interrupt": "Timers",
    }, inplace=True)
    
    system_calls_sum = df[df.index.str.contains('sys')].sum()
    df = df[~df.index.str.contains('sys')]

    df.loc["System Calls"] = system_calls_sum
    
    df.fillna(0, inplace=True)
    
    if 'khugepaged' not in df.index:
        df.loc['khugepaged'] = 0
    df.rename(index={
        "asm_exc_page_fault": "Page Faults",
        "asm_sysvec_apic_timer_interrupt": "Timers",
        "others": "Others",
        "khugepaged": "khugepaged (THP)"
    }, inplace=True)
    
    return df
    
def merge_per_thp_per_test(per_thp_test_dfs, key):
    merged = pd.DataFrame()
    for df in per_thp_test_dfs:
        # df = df.drop('asm_sysvec_apic_timer_interrupt')
        merged = pd.concat([merged, df], axis=1)
    merged.fillna(0,inplace=True)
    

    # get relative base
    base_sum = merged[key].sum()
    relative = merged / base_sum

    small_idx = relative < 0.009

    percent_cleaned = relative[~small_idx].dropna(how='all')
    # append those small entries to the last entry
    other_sums = relative[small_idx].sum(axis=0).rename('others')
    percent_cleaned = percent_cleaned._append(other_sums)

    percent_cleaned.index = np.array([element.lstrip("__") for element in percent_cleaned.index])
    
    print(percent_cleaned)
    # print(merged)

    return percent_cleaned
    # return percent_cleaned, merged, atlair_reprocessed

def all_merge(raws_alltests, thp):
    merged = pd.DataFrame()
    for df in raws_alltests:
        merged = pd.concat([merged, df], axis=1)
    merged.fillna(0,inplace=True)

    merged.to_csv(f'merged_unified_raw_{thp}.csv')

    print('raw result saved to', f'merged_unified_raw_{thp}.csv')
    
def transform_to_atlair(all_tests, group_factor, thp):

    merged = pd.DataFrame()
    for df in all_tests:
        altlair_form_df = reprocess_with_category(df)
        merged = pd.concat([merged, altlair_form_df], axis=1)
    merged.fillna(0,inplace=True)

    print(merged)
    merged.to_csv(f'merged_relative_{thp}.csv')
    print('relative result saved to ', f'merged_relative_{thp}.csv')

    df_melted = merged.reset_index().melt(id_vars='index')


    df_melted['system'] = df_melted['variable'].apply(lambda x: 'x86' if 'radix' in x else 'ECPT')
    df_melted['workload'] = df_melted['variable'].apply(lambda x: x.split('_')[0].upper())

    df_melted['workload'] = df_melted['workload'].replace(
        {   
            'PAGERANK':'PR', 
            'SYSBENCH' : 'Sysbench',
            'REDIS' : 'Redis',
            'MEMCACHED' : 'Memcached',
            'POSTGRES' : 'Postgres',
        }
    )

    df_melted.rename(columns={'index': 'function', 'value': 'instruction'}, inplace=True)
    transformed_df = df_melted[['workload', 'system', 'instruction', 'function']]

    print(transformed_df)

    out_file = os.path.join('../RethinkVM-prep/', 'data', f'kern_inst_{thp}_unified.csv')
    transformed_df.to_csv(out_file, index=False)
    print("save to ", out_file)

    print(transformed_df[transformed_df['function'] == 'irq_entries_start'])

if __name__ == "__main__":
    
    sim_inst_df = read_sim_inst_csv("run_scripts/sim_inst.csv")

    archs = [
        "radix",
        "ecpt",
    ]

    THP_options = [
        "never",
        # "always",
    ]

    tests = [
        "graphbig_bfs" ,
        "graphbig_dfs" ,
        "graphbig_dc" ,
        "graphbig_sssp" ,
        "graphbig_cc" ,
        "graphbig_tc" ,
        "graphbig_pagerank" ,
        "sysbench" ,
        "gups",
        "redis",
        "memcached",
        "postgres",
    ]
    
    for thp in THP_options:
        all_tests_percents = []
        raws = []
        atlair_dfs = []
        for test in tests:  
            per_test = []
            for kernel in archs:
                df, running_loading_and_unified = get_result_per_kernel_thp_test(kernel, thp, test, sim_inst_df)
                per_test.append(df)
                raws.append(running_loading_and_unified)
            
            
            percent_df = merge_per_thp_per_test(per_test, per_test[0].columns[0])
            all_tests_percents.append(percent_df)
    
        all_merge(raws, thp)

        transform_to_atlair(all_tests_percents, group_factor=len(archs), thp=thp)
    