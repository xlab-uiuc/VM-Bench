import argparse
import os
import shutil
import glob
from matplotlib import pyplot as plt
import numpy as np

import pandas as pd
from scipy.stats import gmean

kernel_names = [
    "5.15.0-gen-x86",
    "5.15.0-vanilla",
]

THP_options = [
    "THP_always",
    "THP_never",
]

# read_LEBench_perf_from_csv("5.15.0-vanilla/5.15.0-vanilla_THP_always_LEBench_2023-11-15-16:09:33.csv")

target_folder = "../RethinkVM-prep/data/raw_data/xeon/"

def copy_LEBench():
    for kernel in kernel_names:
        for thp in THP_options:
            # paper_results/5.15.0-gen-x86/5.15.0-gen-x86_THP_always_LEBench.csv
            folder_path = os.path.join('paper_results', kernel, 'LEBench')
            file_name = f'{kernel}_{thp}_LEBench.csv'
            file_path = os.path.join(folder_path, file_name)
            print('copying: ', file_path, ' to ', target_folder)
            shutil.copy(file_path, target_folder)

def get_files_with_prefix(directory, prefix):
    # Construct the search pattern
    # add _2 to filter out latency
    pattern = os.path.join(directory, prefix + '_2' +'*.csv')
    
    # Use glob to find files that match the pattern
    files = glob.glob(pattern)
    files.sort()
    return files

def replace_extremes(row):
    max_val = row.max()
    min_val = row.min()
    row[row == max_val] = np.nan
    row[row == min_val] = np.nan
    return row


def plot_normliazed(df, avg, title):
    df_normalized = df.div(avg, axis=0)
    ax = df_normalized.plot(kind='bar', figsize=(12, 12))

    plt.xlabel('Metrics')
    plt.ylabel('Values')
    plt.title(title)

    # plt.show()
    print('plot saved to: ', title + '.png')
    plt.savefig(title + '.png')

def extract_LEBench_latency_per_iter(df, start_col_name='times', end_col_name='avg_latency'):
    # print(df.head())
    column_names = df.columns.tolist()

    start_index = column_names.index(start_col_name) + 1  # +1 because we want to start after 'times'
    end_index = column_names.index(end_col_name)  # end_index is exclusive in slicing

    # Extract the columns
    extracted_columns = column_names[start_index:end_index]

    per_iter_df = df[extracted_columns]
    per_iter_df.index = df.index

    return per_iter_df.copy()


def plot_df(csv_path, avg_col='avg_latency', start_col_name='times', end_col_name='avg_latency'):
    df = pd.read_csv(csv_path, index_col=0)

    per_iter_df = extract_LEBench_latency_per_iter(df, start_col_name, end_col_name)
    
    per_iter_df[avg_col] = per_iter_df.mean(axis=1)
    per_iter_df['geo_mean'] = gmean(per_iter_df, axis=1)
    # Apply the function to each row
    plot_normliazed(per_iter_df, per_iter_df[avg_col], title=csv_path)

    return per_iter_df

def plot_df_remove_max_min(csv_path):
    df = pd.read_csv(csv_path, index_col=0)

    per_iter_df = extract_LEBench_latency_per_iter(df)
    
    per_iter_df = per_iter_df.apply(replace_extremes, axis=1)
    # print(per_iter_df.head())

    per_iter_mean = per_iter_df.mean(axis=1)
    per_iter_df['avg_latency'] = per_iter_mean
    # Apply the function to each row
    plot_normliazed(per_iter_df, per_iter_mean, title=csv_path + '_remove_max_min')

    return per_iter_df

def copy_common(exp_name, tag, copy, avg_col, start_col_name, end_col_name):
    for kernel in kernel_names:
        for thp in THP_options:
            file_prefix = f'{kernel}_{thp}_{exp_name}'
            folder = os.path.join('paper_results', kernel)
            result_path_list = get_files_with_prefix(folder, file_prefix)

            last_result = result_path_list[-1]
            print(last_result)

            per_iter_df = plot_df(last_result, avg_col, start_col_name, end_col_name)

            saved_path = last_result + 'geo_mean'
            per_iter_df.to_csv(saved_path, index=True)


            target_path = os.path.join(target_folder, file_prefix + f'_{tag}' + '_.csv')
            
            if copy:
                print('copying: ', saved_path, ' to ', target_path)
                shutil.copy(saved_path, target_path)

            print('')

def copy_LEBench_latency():
    for kernel in kernel_names:
        for thp in THP_options:
            # paper_results/5.15.0-gen-x86/5.15.0-gen-x86_THP_never_LEBench_latency_2023-11-19-08-27-27.csv
            file_prefix = f'{kernel}_{thp}_LEBench_latency'
            folder = os.path.join('paper_results', kernel)
            result_path_list = get_files_with_prefix(folder, file_prefix)

            last_result = result_path_list[-1]
            print(last_result)

            plot_df(last_result)
            df_remove_max_min = plot_df_remove_max_min(last_result)
            remov_max_min_path = last_result + 'remove_max_min'
            print('saving to: ', remov_max_min_path)
            df_remove_max_min.to_csv(remov_max_min_path + 'remove_max_min', index=True)

            target_path = os.path.join(target_folder, file_prefix + '.csv')
            print('copying: ', last_result, ' to ', target_path)
            # shutil.copy(last_result, target_path)

            target_path = os.path.join(target_folder, file_prefix + '_remove_max_min.csv')
            print('copying: ', remov_max_min_path, ' to ', target_path)
            # shutil.copy(remov_max_min_path, target_path)

            print('')


def plot_copy_app(tag, copy):
    copy_common('app', tag, copy,
                avg_col='avg_run_time', start_col_name='avg_load_time', end_col_name='avg_run_time')
    
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--copy', action='store_true', help='Activate copy mode')
    args = parser.parse_args()
    
    # copy_common('LEBench_latency')
    plot_copy_app('7avg', args.copy)

# Note this is not working anymore
# copy_LEBench_latency()