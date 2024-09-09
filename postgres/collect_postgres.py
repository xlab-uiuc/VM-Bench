import subprocess
import os
import re
import pandas as pd
import numpy as np
from scipy.stats import gmean
import argparse

base_dict = {
    "latency average" : 0,
    "tps" : 0,
}


def extract_latencies(file_path, dict_to_update):
    # print('parsing file:', file_path)

    with open(file_path, 'r') as file:
        for line in file:
            for key in dict_to_update.keys():
                if key in line:
                    after_equal = line.split('=')[-1].strip()
                    number = after_equal.split(' ')[0].strip()
                    dict_to_update[key] = float(number)


def get_file_list_from_folder(folder, trailing_key):
    print('folder: {}'.format(folder))
    command = ['bash', '-c', 'ls ' + folder + ' | grep {}'.format(trailing_key) ]
    print('command: {}'.format(' '.join(command)))
    try:
        # Run the grep command and capture the stdout and stderr
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        # Check if the command was successful
        if result.returncode == 0:
            # Return the stdout
            return result.stdout.decode('utf-8').splitlines()
        else:
            # If the command failed, you can optionally handle the error here
            print(f"Error occurred: {result.stderr}")
            return None
    except Exception as e:
        print(f"An error occurred: {e}")
        return None




def get_results(folder):
    print('get results for folder:', folder)
    
    file_list = get_file_list_from_folder(folder, 'Run*')
    print(file_list)
    
    dict_list = []
    for file in file_list:
        file_path = os.path.join(folder, file)
        file_dict = base_dict.copy()
        
        extract_latencies(file_path, file_dict)
        dict_list.append(file_dict)
    
    df = pd.DataFrame(dict_list)
    
    mean_row = df.mean(numeric_only=True)
    geo_mean_row = df.select_dtypes(include=[np.number]).apply(gmean)

    df = df.append(mean_row, ignore_index=True)
    df = df.append(geo_mean_row, ignore_index=True)
    
    df.index = file_list + ['mean', 'geomean']
    print(df)
    
    return df
    


folder_list = [
    'postgres_results/-5.15.0-gen-x86-THP_never-2024-09-04_18-38-52',
    "postgres_results/5.15.0-vanilla-THP_never-2024-09-04_20-00-18"
]

if __name__ == "__main__":
    
    parser = argparse.ArgumentParser(description='An example script with arguments.')
    parser.add_argument('--folder', type=str, help='folder of dynamorio logs. selected with ls | grep _dyna.log | grep -v png')
    
    args = parser.parse_args()
    
    if args.folder:
        folder_list = [args.folder]
    
    csv_paths = []
    for folder in folder_list:
        df = get_results(folder)
        
        csv_path = os.path.join(folder, 'result.csv')
        df.to_csv(csv_path)
        csv_paths.append(csv_path)
        
    print('\n'.join(csv_paths))