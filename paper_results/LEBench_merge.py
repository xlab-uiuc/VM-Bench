import argparse
import re
import shutil
from matplotlib import pyplot as plt
import pandas as pd
import numpy as np
import csv
import os
import glob

def read_LEBench_perf_from_csv(path):
    runtimes = []
    bench_names = []
    with open(path, 'r') as file:
        # Create a CSV reader object
        reader = csv.reader(file)
        for row in reader:
            # Access the data in each row
            # example format:       
            # ['       cpu          kbest:', '0.003007388', '']
            # ['       cpu        average:', '0.003009014', '0.000001458']
            bench_entry = row[0]
            if ("average" in bench_entry):
                runtimes.append(float(row[1]))

                cleaned = bench_entry.replace('average:', '').strip()
                cleaned = cleaned.replace('_', ' ')
                bench_names.append(cleaned)

    # bench_names = bench_names[:5] # only keep the first 5 benchmarks
    # runtimes = runtimes[:5]
    return np.array(bench_names), np.array(runtimes) 

def extract_datetime_from_path(file_path):
    # Regular expression to match the date and time in the file path
    # This pattern matches strings like 2023-11-17-16-30-48
    pattern = r'\d{4}-\d{2}-\d{2}-\d{2}-\d{2}-\d{2}'

    # Search for the pattern in the file path
    match = re.search(pattern, file_path)
    if match:
        datetime_str = match.group()
        # Parse the date-time string into a datetime object
        # Adjust the format string according to your needs
        return datetime_str
    else:
        return 'None'


def merge_results(result_path_list):
    # result_list is a list of (bench_names, runtimes) tuples
    # merge the results into a single dataframe
    # return the merged dataframe
    merged = pd.DataFrame()


    for path in result_path_list:
        bench_names, runtimes = read_LEBench_perf_from_csv(path)
        datatime_str = extract_datetime_from_path(path)

        new_df = pd.DataFrame(runtimes, index=bench_names, columns=[datatime_str])
        merged = pd.concat([merged, new_df], axis=1)
        
    # append the mean column
    merged['mean'] = merged.mean(axis=1)   
    return merged

def get_files_with_prefix(directory, prefix):
    # Construct the search pattern
    # add _2 to filter out latency
    pattern = os.path.join(directory, prefix + '_2' +'*')
    
    # Use glob to find files that match the pattern
    files = glob.glob(pattern)
    files.sort()
    return files

def plot_merged_result(df, title):
    df_normalized =  df.div(df['mean'], axis=0)
    ax = df_normalized.plot(kind='bar', figsize=(12, 12))

    plt.xlabel('Metrics')
    plt.ylabel('Values')
    plt.title(title)

    # plt.show()
    plt.savefig(title + '.png')

def merge_results_per_kernel_thp(kernel, thp):
    folder = kernel
    file_prefix = f'{kernel}_{thp}_LEBench'

    result_path_list = get_files_with_prefix(folder, file_prefix)
    merged = merge_results(result_path_list)

    # print(merged)
    csv_path = os.path.join(folder, f'{kernel}_{thp}_LEBench.csv')
    merged.to_csv(csv_path)
    
    print("merge:\n\t", '\n\t'.join(result_path_list))
    print("to: ", csv_path)

    plot_merged_result(merged, title=f'{kernel}_{thp}_LEBench')
    return csv_path

if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument('--copy', action='store_true', help='Activate copy mode')
    args = parser.parse_args()

    kernel_names = [
        "5.15.0-gen-x86",
        "5.15.0-vanilla",
    ]

    THP_options = [
        "THP_always",
        "THP_never",
    ]

    # read_LEBench_perf_from_csv("5.15.0-vanilla/5.15.0-vanilla_THP_always_LEBench_2023-11-15-16:09:33.csv")

    output_files = []
    for kernel in kernel_names:
        for thp in THP_options:
            csv_path = merge_results_per_kernel_thp(kernel, thp)
            output_files.append(csv_path)
    
    print("output_files: ", output_files)

    output_folder = "../../RethinkVM-prep/data/raw_data/xeon/"

    if args.copy:
        for file in output_files:
            shutil.copy(file, output_folder)
    
