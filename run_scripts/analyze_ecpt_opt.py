import glob
import os
import re
import matplotlib.pyplot as plt
import matplotlib
import numpy as np
import pandas as pd
# matplotlib.use("TkAgg")

color = [
	# ['#1D3557', '#000000', '///'],
	# ['#A8DADC', '#000000', '///'],
	# ['#073B3A', '#000000', 'xxx'],
	# ['#95B46A', '#000000', 'xxx'],
	# ['#B87A00', '#000000', '...'],
	# ['#FFC800', '#000000', '...'],
	# ['#8C2F39', '#000000', '|||'],
	# ['#FBA69D', '#000000', '|||'],

	# ['#A8DADC', '#000000', '/'],
	# ['#FFFFFF', '#000000', '/'],
	# ['#95B46A', '#000000', 'x'],
	# ['#FFFFFF', '#000000', 'x'],
	# ['#FFC800', '#000000', '.'],
	# ['#FFFFFF', '#000000', '.'],
	# ['#FBA69D', '#000000', '|'],
	# ['#FFFFFF', '#000000', '|'],
]

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
        merged = pd.concat([merged, df], axis=1)
    merged.fillna(0,inplace=True)
    
    # print(merged)

    # get relative base
    base_sum = merged[key].sum()
    relative = merged / base_sum

    # print(relative)
    small_idx = relative < 0.004

    percent_cleaned = relative[~small_idx].dropna(how='all')
    # append those small entries to the last entry
    other_sums = relative[small_idx].sum(axis=0).rename('others')
    percent_cleaned = percent_cleaned._append(other_sums)
    percent_cleaned.index = np.array([element.lstrip("__") for element in percent_cleaned.index])

    print(percent_cleaned)
    
    return percent_cleaned

# def get_result_per_kernel_thp_test(kernel, thp, test_name):
#     folder = f'kernel_inst_high_level'
#     file_prefix = f'{kernel}_{thp}_{test_name}'

#     # example radix_never_graphbig_tc_walk_log.bin.kern_inst.folded.high_level.csv
#     # paper_results/5.15.0-vanilla/LEBench/
#     result_path = os.path.join(folder, file_prefix + '_walk_log.bin.kern_inst.folded.high_level.csv')

#     if 'graphbig' in test_name:
#         test_name = test_name.replace('graphbig_', '')
#     df = pd.read_csv(result_path, header=None, names=['symbol', f'{kernel}_{test_name}'])
#     df.set_index('symbol', inplace=True)
#     return df

def get_result_per_thp_tag(parent_folder, thp, tag, arch, bench):
    folder = os.path.join(parent_folder, tag)
    file_prefix = f'{arch}_{thp}_{bench}*high_level.csv'


    glob_pattern = os.path.join(folder, file_prefix)
    # print(glob_pattern)
    files = [file_name for file_name in glob.glob(glob_pattern)]
    
    if len(files) == 0:
        print(f"No files found for {glob_pattern}")
        return None

    result_path = files[0]

    print(result_path)
    # print('\n'.join(result_path_list))
    df = pd.read_csv(result_path, header=None, names=['symbol', f'{thp}_{translate_tag[tag]}'])
    df.set_index('symbol', inplace=True)
    return df
    # print(merged)

def get_stas(df):
    pf_time = df.loc['asm_exc_page_fault'].sum()
    total_time = df.sum().sum()

    return pf_time, total_time

def show_relative_plot(pf_df, base, thp):
    # plt.figure(figsize=(10, 6))  # Set the size of the figure
    plt.rcParams.update({'font.family': 'Times New Roman' })
    plt.rcParams['font.size'] = 24
    print("base ", base)
    relative_df = pf_df / base 
    print(relative_df)

    # relative_df = relative_df.T
    print(relative_df)
    relative_df = relative_df.iloc[::-1]
    # relative_df.index = ['4KB', 'THP']
    #1D3557', '#000000', '///'],
	# ['#A8DADC', '#000000', '///'],
	# ['#073B3A
    # relative_df.plot(kind="barh", figsize=(6, 3), color=["#1D3557", "#A8DADC", "#00c04b"], width=0.8)
    # ax = relative_df.plot(kind="barh", color=['#96ceb4'], edgecolor="Black", figsize=(6, 3), width=0.9) rgbkymc
    ax = relative_df.T.plot(kind="barh", color=["#96ceb4", "#A8DADC", "#00c04b"], edgecolor="Black", figsize=(6, 3), width=0.9)
    # print(relative_df.columns)
    # plt.title("Comparison of optimization effects on PF handler instructions")
    # plt.ylabel("Norm. # of instructions")

    plt.xlabel("Norm. # of instructions")
    plt.xticks(rotation=0)
    ax.get_legend().set_visible(False)
    ax.get_yaxis().set_visible(False)
    # plt.legend(title="Optimizations")
    # plt.legend(bbox_to_anchor=(0.5, 1.15), loc='upper center', ncol=3)
    # plt.legend(bbox_to_anchor=(0.5, 1.27), loc='upper center', ncol=1, fontsize=22, frameon=False)

    # plt.legend(loc='upper center', ncol=3)
    # plt.legend(None)
    plt.setp(ax.yaxis.get_majorticklabels(), rotation=340, ha="right", rotation_mode="anchor") 
    plt.tight_layout()
    plt.subplots_adjust(top=0.82)
    path = f'opt_group_effect_{thp}.svg'
    plt.show()
    print("save path " , path)
    plt.savefig(path)


    # plt.gcf().set_size_inches(1, 1)
    # plt.gca().set_xlim(0, 0.0000001)
    # plt.gca().set_ylim(0, 0.0000001)   
    # plt.gca().set_xticks([])
    # plt.gca().set_yticks([])
    # plt.gca().spines['top'].set_visible(False)
    # plt.gca().spines['right'].set_visible(False)
    # plt.gca().spines['bottom'].set_visible(False)
    # plt.gca().spines['left'].set_visible(False)
    # ax.axis('off')
    # ax.get_legend().set_visible(True)
    # handles, labels = ax.get_legend_handles_labels()
    # ax.legend(handles[::-1], labels[::-1], bbox_to_anchor=(.5, 1.35), loc='upper center', ncol=3, fontsize="15")
    # legend = plt.legend()
    # plt.show() 
    path = f'opt_group_effect_{thp}.legend.svg'
    # print("save path " , path)
    # plt.savefig(path, transparent=True)
    handles, labels = ax.get_legend_handles_labels()
    fig, ax = plt.subplots(1)
    fig.set_size_inches(4, .5)
    ax.legend(handles=handles[::-1], labels=labels[::-1], loc='upper center', ncol=3, fontsize="15", frameon=False)
    ax.axis('off')
    fig.savefig(path, bbox_inches='tight')


    # plt.rcParams.update({'font.family': 'Times New Roman' })

    # categories = merged.columns
    
    # labels = merged.index
    # prev = np.zeros(len(categories))
    # for i in range(len(labels)):
    #     cur_data = np.array(merged.iloc[i])        
    #     plt.bar(categories, cur_data, bottom=prev, width=0.5, label=labels[i])
    #     prev += cur_data

    # plt.title(f"Kernel Time Distribution for on {thp}")  # Add a title to the chart
    # plt.legend(loc='upper center', bbox_to_anchor=(0.5, -0.1), ncol=2)  # Add a legend
    # plt.tight_layout()
    # save_path = f'{thp}_kern_inst.svg'
    # print("save to ", save_path)
    # # # plt.show(block=True)
    # plt.savefig(save_path)


if __name__ == '__main__':
    plt.ion() 

    archs = [
        # "radix",
        "ecpt",
    ]

    THP_options = [
        "never",
        "always",
    ]

    # tests = [
    #     "graphbig_bfs" ,
    #     "graphbig_cc" ,
    #     "graphbig_dc" ,
    #     "graphbig_dfs" ,
    #     "graphbig_sssp" ,
    #     "graphbig_tc" ,
    #     "graphbig_pagerank" ,
    #     "sysbench" ,
    #     "gups",
    # ]

    tag = [
        "no_iter_no_place_opt",
        # "no_iter_no_place_opt_run2",
        # "no_iter",
        # "withIter_noPlace",
        # "withIter_noPlace_run2",
        # "withIter_noPlace_run2",
        "no_iter0",
        "withIter_withPlace"
        # "default",
    ]

    translate_tag = {
        "no_iter_no_place_opt": "baseline",
        "no_iter_no_place_opt_run2": "base 2",

        "withIter_noPlace" : "Iterator only",
        "withIter_noPlace_run2" : "iterator only",
        "no_iter" : "__With placement opt",
        "no_iter0" : "+ VMA opt",
        "default": "thp_eligible + Iterator",
        "withIter_withPlace" : "+ iterator opt"
    }

    translated_tags = [translate_tag[t] for t in tag]

    pf_time_data = {}
    total_time_data = {}
    
    all_thp_dfs = []
    for thp in THP_options:
        pf_time_data[thp] = []
        total_time_data[thp] = []
        for t in tag:
            df = get_result_per_thp_tag('kernel_inst_loading', thp, t, 'ecpt', 'graphbig_bfs')
            
            pf_time, total_time = get_stas(df)
            pf_time_data[thp].append(pf_time)
            total_time_data[thp].append(total_time)

        per_thp_df = pd.DataFrame(pf_time_data[thp])
        per_thp_df.index = translated_tags
        
        
        if thp == 'never':
            per_thp_df.columns = ['4KB']
        elif thp == 'always':
            per_thp_df.columns = ['THP']
        
        print(per_thp_df)
        show_relative_plot(per_thp_df, per_thp_df.loc['baseline'], thp)
    #     all_thp_dfs.append(per_thp_df)
    
    # pf_df = pd.concat(all_thp_dfs, axis=1)
    # print(pf_df)
    #     # show_relative_plot_single(per_thp_df, per_thp_df.loc['base'], thp)
    # # pf_df = pd.DataFrame(pf_time_data)
    # # pf_df.index = translated_tags

    # # print(pf_df)
    # show_relative_plot(pf_df, pf_df.loc['baseline'])
    