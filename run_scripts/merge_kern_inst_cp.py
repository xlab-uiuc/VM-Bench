import glob
import os
import re
import matplotlib.pyplot as plt
import matplotlib
import numpy as np
import pandas as pd
# matplotlib.use("TkAgg")

def read_kernel_symbols(file_path='/proc/kallsyms'):
    symbols2tiime = {}
    
    try:
        with open(file_path, 'r') as file:
            for line in file:
                parts = line.strip().split()
                if len(parts) >= 3:
                    address, type, name = parts[:3]
                    symbols2tiime[name] = 0
                    # print(f"Address: {address}, Type: {type}, Name: {name}")
    except FileNotFoundError:
        print(f"File not found: {file_path}")
    except PermissionError:
        print(f"Permission denied. You might need to run this as root to access {file_path}.")

    return symbols2tiime

def extract_number_at_end(line):
    match = re.search(r'\d+$', line)
    if match:
        return int(match.group())
    else:
        return None

def split_line_remove_number(line):
    # Remove the trailing number using regular expression
    line_without_number = re.sub(r'\s*\d+$', '', line)
    # Split the line by semicolon
    parts = line_without_number.split(';')
    return parts


def find_symbol(line, symbols):
    blacklisted_symbols = ['entry_SYSCALL_64', 'do_syscall_64',
                           'entry_SYSCALL_64_after_hwframe', 'strcmp', 'memmove', 'memset']
    parts = split_line_remove_number(line)
    for part in parts:
        if part in symbols and (part not in blacklisted_symbols):
            return part
    return None

def dict_to_df(symbols, column):
    df = pd.DataFrame.from_dict(symbols, orient='index')
    # df.reset_index(inplace=True)
    # df.columns = ['symbol', 'time']
    df.columns = [column]
    df = df[df != 0].dropna()
    # print(df)
    return df

def get_kernel_component_time(folded_file_path, kernel_symbols, column_key):

    with open(folded_file_path, 'r') as file:
        for line in file:
            number = extract_number_at_end(line)
            symbol = find_symbol(line, kernel_symbols)
            if symbol:
                kernel_symbols[symbol] += number

    return dict_to_df(kernel_symbols, column_key)

# color = [
# 	# ['#1D3557', '#000000', '///'],
# 	# ['#A8DADC', '#000000', '///'],
# 	# ['#073B3A', '#000000', 'xxx'],
# 	# ['#95B46A', '#000000', 'xxx'],
# 	# ['#B87A00', '#000000', '...'],
# 	# ['#FFC800', '#000000', '...'],
# 	# ['#8C2F39', '#000000', '|||'],
# 	# ['#FBA69D', '#000000', '|||'],

# 	['#A8DADC', '#000000', '/'],
# 	['#FFFFFF', '#000000', '/'],
# 	['#95B46A', '#000000', 'x'],
# 	['#FFFFFF', '#000000', 'x'],
# 	['#FFC800', '#000000', '.'],
# 	['#FFFFFF', '#000000', '.'],
# 	['#FBA69D', '#000000', '|'],
# 	['#FFFFFF', '#000000', '|'],
# ]

def merge_cross_kernel(symbol_to_time_list, kernels, key_col='mean'):
    avg_list = [df[key_col].copy() for df in symbol_to_time_list]
    all_kernel_perf = pd.concat(avg_list, axis=1)

    all_kernel_perf.columns = kernels
    all_kernel_perf.fillna(0,inplace=True)
    return all_kernel_perf

def process_cross_kernel_perf_breakdown(all_kernel_perf, kernels):
    all_kernel_perf.sort_index(inplace=True)

    print(all_kernel_perf)
    label = all_kernel_perf.index
    values = all_kernel_perf[kernels]

    percentage = values / values.sum(axis=0)
    small_idx = percentage < 0.004

    # remove entries that are too small
    percent_cleaned = percentage[~small_idx].dropna(how='all')
    # append those small entries to the last entry
    other_sums = percentage[small_idx].sum(axis=0).rename('others')
    percent_cleaned = percent_cleaned._append(other_sums)

    percent_cleaned.index = np.array([element.lstrip("__") for element in percent_cleaned.index])
    
    percent_cleaned.columns = ['EMT-Radix', 'Vanilla Linux']
    return percent_cleaned

def show_plot(all_kernel_perf, kernels, thp, test_name):
    plt.figure(figsize=(5, 4))  # Set the size of the figure
    plt.rcParams.update({'font.family': 'Times New Roman' })

    clean_all_kernel_perf = process_cross_kernel_perf_breakdown(all_kernel_perf, kernels)
    print(clean_all_kernel_perf)

    categories = clean_all_kernel_perf.columns
    
    labels = clean_all_kernel_perf.index
    prev = np.zeros(len(categories))
    for i in range(len(labels)):
        cur_data = np.array(clean_all_kernel_perf.iloc[i])        
        plt.bar(categories, cur_data, bottom=prev, width=0.5, label=labels[i])
        prev += cur_data

    plt.title(f"Kernel Time Distribution for {test_name} on {thp}")  # Add a title to the chart
    plt.legend(loc='upper center', bbox_to_anchor=(0.5, -0.1), ncol=2)  # Add a legend
    plt.tight_layout()
    save_path = f'{thp}_{test_name}.svg'
    print("save to ", save_path)
    # plt.show(block=True)
    plt.savefig(save_path)

def get_files_with_prefix(directory, prefix):
    pattern = os.path.join(directory, prefix + '*' + 'out_selected.folded')
    # print(pattern)
    # Use glob to find files that match the pattern
    files = glob.glob(pattern)
    files.sort()
    return files

def get_test_keyword(path, test_name):
    start_idx = path.index(test_name)
    path = path[start_idx:]
    path = path.replace('_out_selected.folded', '')
    return path

def merge_results(result_path_list, test_name):
    # result_list is a list of (bench_names, runtimes) tuples
    # merge the results into a single dataframe
    # return the merged dataframe
    merged = pd.DataFrame()

    sybmol2time = read_kernel_symbols()
    for path in result_path_list:
        keyword = get_test_keyword(path, test_name)
        kernel_time_df = get_kernel_component_time(path, sybmol2time.copy(), keyword)
        
        merged = pd.concat([merged, kernel_time_df], axis=1)
        
    # append the mean column
    merged.fillna(0,inplace=True)
    merged['mean'] = merged.mean(axis=1) 
    return merged

def merge_per_thp_per_test(per_thp_test_dfs, key):
    merged = pd.DataFrame()
    for df in per_thp_test_dfs:
        df = df.drop('asm_sysvec_apic_timer_interrupt')
        merged = pd.concat([merged, df], axis=1)
    merged.fillna(0,inplace=True)
    
    # print(merged)

    # get relative base
    base_sum = merged[key].sum()
    relative = merged / base_sum

    # print(relative)
    # print(relative)
    small_idx = relative < 0.009

    percent_cleaned = relative[~small_idx].dropna(how='all')
    # append those small entries to the last entry
    other_sums = relative[small_idx].sum(axis=0).rename('others')
    percent_cleaned = percent_cleaned._append(other_sums)
    percent_cleaned.index = np.array([element.lstrip("__") for element in percent_cleaned.index])

    # print(percent_cleaned)
    
    return percent_cleaned, merged

def get_result_per_kernel_thp_test(kernel, thp, test_name):
    folder = f'kernel_inst'
    file_prefix = f'{kernel}_{thp}_{test_name}'

    # if kernel == 'ecpt' and thp == 'always':
    #     folder = os.path.join('kernel_inst_loading', 'withIter_withPlace')

    # example radix_never_graphbig_tc_walk_log.bin.kern_inst.folded.high_level.csv
    # paper_results/5.15.0-vanilla/LEBench/
    result_path = os.path.join(folder, file_prefix + '_walk_log.bin.kern_inst.folded.high_level.csv')

    if 'graphbig' in test_name:
        test_name = test_name.replace('graphbig_', '')
    col = f'{test_name}_{kernel}'
    # col = ''
    # if thp == 'always':
    #     col = f'{test_name}_{kernel}_THP'
    # else:
    #     col = f'{test_name}_{kernel}_4KB'
    
    print(result_path)

    df = pd.read_csv(result_path, header=None, names=['symbol', file_prefix])
    df.set_index('symbol', inplace=True)
    return df

    # print('\n'.join(result_path_list))

    # print(merged)

def show_relative_plot(per_thp_reults, thp):
    plt.figure(figsize=(15, 4))  # Set the size of the figure
    # plt.rcParams.update({'font.family': 'Times New Roman' })

    merged = pd.DataFrame()
    for df in per_thp_reults:
        merged = pd.concat([merged, df], axis=1)
    merged.fillna(0,inplace=True)

    print(merged.T)

    categories = merged.columns
    
    labels = merged.index
    prev = np.zeros(len(categories))
    for i in range(len(labels)):
        cur_data = np.array(merged.iloc[i])        
        plt.bar(categories, cur_data, bottom=prev, width=0.5, label=labels[i])
        prev += cur_data

    plt.title(f"Kernel Time Distribution for on {thp}")  # Add a title to the chart
    plt.legend(loc='upper center', bbox_to_anchor=(0.5, -0.1), ncol=2)  # Add a legend
    plt.tight_layout()
    save_path = f'{thp}_kern_inst.svg'
    print("save to ", save_path)
    # # plt.show(block=True)
    plt.savefig(save_path)

def find_config_name(path):
    start_idx = path.index('_')
    config_name = path[start_idx+1:]
    return config_name

def find_bench_name(path):
    start_idx = path.index('_')
    bench = path[:start_idx]
    return bench

def print_all_tests(all_tests, group_factor, thp):

    merged = pd.DataFrame()
    for df in all_tests:
        merged = pd.concat([merged, df], axis=1)
    merged.fillna(0,inplace=True)

    print(merged)

    num_groups = len(merged.columns) // group_factor


    out_file = os.path.join('../RethinkVM-prep/', 'data', f'kern_inst_{thp}.data')
    with open(out_file, 'w') as kern_inst_file:
        print("# total bechmarks: ", num_groups, file=kern_inst_file)

        for i in range(num_groups):
            group_df = merged.iloc[:, i*group_factor : (i+1)*group_factor]
            benchname = find_bench_name(group_df.columns[0])
            group_df.columns = [find_config_name(col) for col in group_df.columns]


            # seperator for gnuplot 
            print(file=kern_inst_file)
            print(file=kern_inst_file)
            print(f"# {benchname}", file=kern_inst_file)
            print(f"kernel_routines".ljust(1), group_df.T.to_string(index=True, header=True), file=kern_inst_file)
    
    print("save to ", out_file)


def print_all_tests(all_tests, group_factor, thp):

    merged = pd.DataFrame()
    for df in all_tests:
        merged = pd.concat([merged, df], axis=1)
    merged.fillna(0,inplace=True)

    print(merged)

    df_melted = df.reset_index().melt(id_vars='index')

    

    df_melted['system'] = df_melted['variable'].apply(lambda x: 'x86' if 'radix' in x else 'ECPT')
    df_melted['workload'] = df_melted['variable'].apply(lambda x: x.split('_')[0].upper())

    df_melted.rename(columns={'index': 'function', 'value': 'instruction'}, inplace=True)
    transformed_df = df_melted[['workload', 'system', 'instruction', 'function']]

    print(transformed_df)
    # num_groups = len(merged.columns) // group_factor


    # out_file = os.path.join('../RethinkVM-prep/', 'data', f'kern_inst_{thp}.data')
    # with open(out_file, 'w') as kern_inst_file:
    #     print("# total bechmarks: ", num_groups, file=kern_inst_file)

    #     for i in range(num_groups):
    #         group_df = merged.iloc[:, i*group_factor : (i+1)*group_factor]
    #         benchname = find_bench_name(group_df.columns[0])
    #         group_df.columns = [find_config_name(col) for col in group_df.columns]


    #         # seperator for gnuplot 
    #         print(file=kern_inst_file)
    #         print(file=kern_inst_file)
    #         print(f"# {benchname}", file=kern_inst_file)
    #         print(f"kernel_routines".ljust(1), group_df.T.to_string(index=True, header=True), file=kern_inst_file)
    
    # print("save to ", out_file)

def transform_to_atlair(all_tests, group_factor, thp):

    merged = pd.DataFrame()
    for df in all_tests:
        merged = pd.concat([merged, df], axis=1)
    merged.fillna(0,inplace=True)

    print(merged)
    merged.to_csv(f'merged_relative_{thp}.csv')
    print('relative result saved to ', f'merged_relative_{thp}.csv')

    df_melted = merged.reset_index().melt(id_vars='index')


    df_melted['system'] = df_melted['variable'].apply(lambda x: 'x86' if 'radix' in x else 'ECPT')
    df_melted['workload'] = df_melted['variable'].apply(lambda x: x.split('_')[0].upper())

    df_melted['workload'] = df_melted['workload'].replace({'PAGERANK':'PR', 'SYSBENCH' : 'Sysbench'})

    df_melted.rename(columns={'index': 'function', 'value': 'instruction'}, inplace=True)
    transformed_df = df_melted[['workload', 'system', 'instruction', 'function']]

    print(transformed_df)

    out_file = os.path.join('../RethinkVM-prep/', 'data', f'kern_inst_{thp}_harsh_iterator.csv')
    transformed_df.to_csv(out_file, index=False)
    print("save to ", out_file)

    print(transformed_df[transformed_df['function'] == 'irq_entries_start'])

def all_merge(raws_alltests, thp):
    merged = pd.DataFrame()
    for df in raws_alltests:
        merged = pd.concat([merged, df], axis=1)
    merged.fillna(0,inplace=True)

    
    merged.to_csv(f'merged_{thp}.csv')

    print('raw result saved to', f'merged_{thp}.csv')

if __name__ == '__main__':
    plt.ion() 

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
        # "sysbench" ,
        # "gups",
    ]

    
    for thp in THP_options:
        per_thp = []
        for test in tests:  
            per_thp_test = []
            for kernel in archs:
                df = get_result_per_kernel_thp_test(kernel, thp, test)
                print(df)
                per_thp_test.append(df)
            key = f'{kernel}_{thp}_{test}'
            # key = f'radix_{test}'
            # if 'graphbig' in test:
            #     stripped = test.replace('graphbig_', '')
            #     key = f'radix_{stripped}'

            test_df = merge_per_thp_per_test(per_thp_test, key)
            per_thp.append(test_df)

        show_relative_plot(per_thp, thp)
                # perf_df.append(merged)
    # for thp in THP_options:
    # for thp in THP_options:
    #     all_tests = []
    #     raws = []
    #     for test in tests:  
    #         per_test = []
    #         for kernel in archs:
    #             df = get_result_per_kernel_thp_test(kernel, thp, test)
    #             per_test.append(df)

    #         # key = f'radix_{test}'
    #         # if 'graphbig' in test:
    #         #     stripped = test.replace('graphbig_', '')
    #         #     key = f'radix_{stripped}'

    #         test_df, merged_raw = merge_per_thp_per_test(per_test, per_test[0].columns[0])
    #         all_tests.append(test_df)
    #         raws.append(merged_raw)
        
    #     all_merge(raws, thp)

    #     transform_to_atlair(all_tests, group_factor=len(archs), thp=thp)
    
        # per_thp.append(test_df)