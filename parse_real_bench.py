import re
import os
import csv

import pandas as pd

redis_regex_patterns = {
    "read_time": r'reader thread took: ([\d.]+) seconds',
    "read_avg_latency": r'\[READ\] average latency ([\d.]+) us',
    "read_throughput": r'\[READ\] average latency [\d.]+ us throughput ([\d.]+) ops/sec',
    "update_time": r'update took: ([\d.]+) seconds',
    "update_avg_latency": r'\[UPDATE\] average latency ([\d.]+) us',
    "update_throughput": r'\[UPDATE\] average latency [\d.]+ us throughput ([\d.]+) ops/sec',
    "running_phase_time": r'Running phase took: ([\d.]+) seconds',
    "running_phase_throughput": r'Running phase overall throughput: ([\d.]+) ops/sec',
    "total_time": r'Took: ([\d.]+) seconds'
}

memcached_regex_patterns = {
    "running_phase_time": r'Running phase took: ([\d.]+) seconds',
    "running_phase_avg_latency": r'Running phase average latency ([\d.]+) us',
    "running_phase_throughput": r'Running phase average latency [\d.]+ us, throughput ([\d.]+) ops/sec',
    "read_operations": r'\[READ\] ([\d.]+) operations',
    "read_avg_latency": r'\[READ\] [\d.]+ operations, average latency ([\d.]+) us',
    "read_throughput": r'\[READ\] [\d.]+ operations, average latency [\d.]+ us, throughput ([\d.]+) ops/sec',
    "update_operations": r'\[UPDATE\] ([\d.]+) operations',
    "update_avg_latency": r'\[UPDATE\] [\d.]+ operations, average latency ([\d.]+) us',
    "update_throughput": r'\[UPDATE\] [\d.]+ operations, average latency [\d.]+ us, throughput ([\d.]+) ops/sec'
}

postgres_regex_patterns = {
    "running_phase_operations": r'Running phase (\d+) operations took: [\d.]+ seconds',
    "running_phase_time": r'Running phase \d+ operations took: ([\d.]+) seconds',
    "running_phase_avg_latency": r'Running phase average latency ([\d.]+) us',
    "running_phase_throughput": r'Running phase average latency [\d.]+ us, throughput ([\d.]+) ops/sec'
}

def parse_log(log_text, regex_patterns):
    # Dictionary to store the parsed data
    parsed_data = {}
    

    # Parse the log text for each pattern in the dictionary
    for key, pattern in regex_patterns.items():
        match = re.search(pattern, log_text)
        if match:
            parsed_data[key] = float(match.group(1))

    return parsed_data

def get_log_text(log_file, starting_line_key):
    # Open the log file and read the contents
    with open(log_file, 'r') as file:
        log_lines = file.readlines()

    starting_line_idx = 0
    for i, line in enumerate(log_lines):
        if starting_line_key in line:
            starting_line_idx = i
            break


    # Get the log text starting from the starting line
    log_text = ''.join(log_lines[starting_line_idx:])

    return log_text

def select_start_line_key(file_name):
    if "redis" in file_name:
        return "reader thread started"
    
    if "memcached" in file_name:
        return "Running phase took:"
    
    if "postgres" in file_name:
        return "Running phase 2000000 operations"
    
    raise ValueError("Unknown folder type")
    return None

def select_regex(file_name):
    if "redis" in folder:
        return redis_regex_patterns

    if "memcached" in folder:
        return memcached_regex_patterns
    
    if "postgres" in folder:
        return postgres_regex_patterns

    raise ValueError("Unknown folder type")
    return None


def parse_real_bench(log_file):        

    log_text = get_log_text(log_file, select_start_line_key(log_file))

    parsed_data = parse_log(log_text, select_regex(log_file))

    return parsed_data

def write_to_csv(data_list, output_file):
    # Write the list of dictionaries to a CSV file
    if data_list:
        fieldnames = data_list[0].keys()  # Get the fieldnames from the first dictionary
        with open(output_file, 'w', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()  # Write the header
            writer.writerows(data_list)  # Write the data rows

def parse_folder(folder):
    log_files = []

    for file in os.listdir(folder):
        if file.endswith(".txt"):
            log_files.append(os.path.join(folder, file))
    
    log_files.sort()

    print (log_files)
    data_list = []

    for log_file in log_files:
        parsed_data = parse_real_bench(log_file)
        data_list.append(parsed_data)
    
    df = pd.DataFrame(data_list)

    df.loc['mean'] = df.mean()

    df.to_csv(f"{folder}/summary.csv", index=True)

    print(f"Data has been written to {folder}/summary.csv")

if __name__ == "__main__":
    # parsed_data = parse_real_bench("redis_5.15.0-vanilla_THP_never_standalone_iter0.txt")
    # print(parsed_data)

    folder = "test_results/redis"
    parse_folder(folder)

    folder = "test_results/memcached"
    parse_folder(folder)

    folder = "test_results/postgres"
    parse_folder(folder)

