#!/usr/bin/env python3

import bisect
import collections
import glob
import multiprocessing
import os
import re
import shutil
import typing
import subprocess
from typing import List, Tuple
import struct
import argparse
import cProfile

max_insn_bytes = 15 # by intel
USER_PROGRAM_MAGIC = 0xdeadbeef

def filter_text(nm_line):
    # T/t means text(code) symbol
    return len(nm_line) == 3 and nm_line[1].lower() == 't'

def get_symbols(vmlinux):
    result = subprocess.run(['nm', vmlinux], check=True, capture_output=True)
    return map(lambda l: l.strip().split(),
               result.stdout.decode('utf-8').split('\n'))

def get_symbol_table(vmlinux_path: str) -> Tuple[list[int], List[str]]:
    # Construct a func -> addr map
    # ffffffff811745c0 T ZSTD_freeDStream
    # l[0]			  l[1]		l[2]
    selected_text_syms = filter(filter_text, get_symbols(vmlinux_path))

    # map function parse the symbol table from selected text symbols
    # sorted function convert the map object to a list of tuples, sorted by the address  
    text_syms = sorted(map(lambda l: (int(l[0], 16), l[2]), selected_text_syms),
                       key=lambda l: l[0])
    
    sym_addrs = [tup[0] for tup in text_syms]
    sym_names = [tup[1] for tup in text_syms]

    return sym_addrs, sym_names

def is_kernel_addr(addr: int) -> bool:
    return addr >= 0xffff800000000000


def get_next_insn(bin_log_file, arch) -> int:

    # typedef struct MemRecord
    # {
    # 	uint8_t header;
    # 	uint8_t access_rw;
    # 	uint16_t access_cpu;
    # 	uint32_t access_sz;
    # 	uint64_t vaddr;
    # 	uint64_t paddr;
    # 	uint64_t pte;
    # 	uint64_t leaves[PAGE_TABLE_LEAVES];
    # 	/* 64 bytes if ECPT not defined */
    # #ifdef TARGET_X86_64_ECPT
    # 	uint64_t cwt_leaves[CWT_LEAVES];
    # 	uint16_t selected_ecpt_way;
    # 	uint8_t pmd_cwt_header;
    # 	uint8_t pud_cwt_header;
    # 	/* 120 bytes if ECPT defined */
    # #endif
    # } MemRecord;

    if arch == "radix":
        PAGE_TABLE_LEAVES = 4
        # radix: uint8, uint8, uint16, uint32, 3 * uint64, PAGE_TABLE_LEAVES * uint64
        entry_format = '<BBHI3Q{}Q'.format(PAGE_TABLE_LEAVES)
    elif arch == "ecpt":
        PAGE_TABLE_LEAVES = 6
        CWT_LEAVES = 4
        # ecpt: uint8, uint8, uint16, uint32, 3 * uint64, PAGE_TABLE_LEAVES * uint64, CWT_LEAVES * uint64, uint16, uint8, uint8, uint32 (padding)
        entry_format = '<BBHI3Q{}Q{}QHBBI'.format(PAGE_TABLE_LEAVES, CWT_LEAVES)
    else:
        print("Please choose a valid arch")
        exit(1)

    ADDR_POS = 4
    HEADER_POS = 0

    entry_size = struct.calcsize(entry_format)
    print(f"Entry size: {entry_size}")

    prev_user = False

    info_format = '<BBHIQ'
    info_size = struct.calcsize(info_format)
    with open(bin_log_file, 'rb') as file:
        while True:
            chunk = file.read(entry_size)  # Read in 1024-byte chunks
            if not chunk:
                break  # If the chunk is empty, end of file has been reached
            full_parsed_data = struct.unpack(info_format, chunk[:info_size])
            addr = full_parsed_data[ADDR_POS]
            header = chr(full_parsed_data[HEADER_POS])
            
            if header == 'F':
                # only consider instruction executed
                if is_kernel_addr(addr):
                    prev_user = False
                    yield addr
                else:
                    if not prev_user:
                        # print('---- user program ----')
                        yield USER_PROGRAM_MAGIC
                    prev_user = True
    
    return 0



def get_symbol_name_addr2line(vmlinux_path: str, addr: int, symbol_dict) -> str:
    
    if addr in symbol_dict:
        return symbol_dict[addr]
    
    # eu-addr2line -fie vmlinux 0xffffffff81258540 | perl -ne 'print "$1\n" if (/^(\w+)( inlined.*)?$/g)'
    command = f"eu-addr2line -fie {vmlinux_path} {hex(addr)} | perl -ne 'print \"$1\n\" if (/^(\w+)( inlined.*)?$/g)'"
    result = subprocess.run(command, shell=True, check=True, capture_output=True)
    decoded = result.stdout.decode('utf-8').strip()

    # Reverse the lines and join them with ;
    # we need to reverse the lines because the addr2line output is in reverse order of call trace
    concated = ';'.join(decoded.split("\n")[::-1])
    symbol_dict[addr] = concated

    return concated	
    
    
def lookup_symbol(sym_addrs, sym_names, addr, vmlinux_path, symbol_dict) -> str:
    index = bisect.bisect_right(sym_addrs, addr)

    addr2line_name = get_symbol_name_addr2line(vmlinux_path, addr, symbol_dict)
    # print(f"addr: {hex(addr)}  addr2line: {addr2line_name}")

    if index:
        return (sym_addrs[index - 1], sym_names[index - 1], addr2line_name)

    return (0x0, "__UNKNOWN_SYMBOL__", "__UNKNOWN_SYMBOL__")

def stack_engine(start: int, name: str, inline: str, addr: int, stack: list, prev_addr: int, prev_start: int, cntr: int):
    # Not empty and in the same symbol (sequential execution), return
    if len(stack) >= 1 and prev_start == start:
        if stack[-1]["inline"] != inline:
            stack[-1]["inline"] = inline
            return (stack, True)
        return (stack, False)

    # First instruction, must be a function enter
    if addr == start:
        stack.append({
            "ret": prev_addr,
            "start": start,
            "sym": name,
            "inline": inline,
        })
        return (stack, True)

    # May be a jump enter or leave
    for idx, rets in enumerate(reversed(stack)):
        # Get the real index from reversed indexworker
            stack[-1]["inline"] = inline
            return (stack, True)
        # TODO: Probably we can detect jump enter near call?

    # Definitely not a return, warn and continue
    print(f"WARNING: at RIP {hex(addr)} ({hex(start)}:{name}+{hex(addr - start)}) RET {hex(prev_addr)} INSN# {hex(cntr)}: jump into the body of function")
    stack.append({
        "ret": prev_addr,
        "start": start,
        "sym": name,
        "inline": inline,
    })
    return (stack, True)

def split_line_remove_number(line):
    # Remove the trailing number using regular expression
    line_without_number = re.sub(r'\s*\d+$', '', line)
    # Split the line by semicolon
    parts = line_without_number.split(';')
    return parts

def get_high_level_symbol(line):
    blacklisted_symbols = ['entry_SYSCALL_64', 'do_syscall_64', 'do_syscall_x64','do_syscall_x64', '__x86_indirect_thunk_rax',
                           'entry_SYSCALL_64_after_hwframe', 'strcmp', 'memmove', 'memset']
    parts = split_line_remove_number(line)
    for part in parts:
        part = part.strip()
        if part not in blacklisted_symbols:
            return part
    return None

def extract_number_at_end(line):
    match = re.search(r'\d+$', line)
    if match:
        return int(match.group())
    else:
        return None
    
def get_high_level_distribution(flame_path):
    high_level_flame = {}
    with open(flame_path, 'r') as file:
        for line in file:
            number = extract_number_at_end(line)
            high_level_key = get_high_level_symbol(line)
            if high_level_key not in high_level_flame:
                high_level_flame[high_level_key] = 0
            high_level_flame[high_level_key] += number
    
    high_level_path = flame_path + ".high_level.csv"
    print(f"Saving high level flamegraph to {high_level_path}")
    with open(flame_path + ".high_level.csv", 'w') as f:
        for key in high_level_flame:
            print(f"{key},{high_level_flame[key]}", file = f)
    return high_level_path

def produce_flame_folded(vmlinux_path : str, trace_path : str, out_path : str, arch : str):
    (sym_addrs, sym_names) = get_symbol_table(vmlinux_path)

    # Function call stack
    stack = []

    # Previous instruction address
    prev_addr = 0x0

    # Previous function identity
    prev_start = 0x0

    # Count of instruction executed
    cntr = 0

    # Current call chain
    call_chain = ""

    # Flamegraph data
    flame = {}

    symbol_dict = {}
    for addr in get_next_insn(trace_path, arch):
        if addr == USER_PROGRAM_MAGIC:
            # user program execution now, clears kernel stack
            stack = []
            prev_addr = 0x0
            prev_start = 0x0
            call_chain = ""
            continue

        (start, name, inline) = lookup_symbol(sym_addrs, sym_names, addr, vmlinux_path, symbol_dict)
        # print(f"{hex(start)} {hex(addr)} {name} {inline}")
        
        (stack, changed) = stack_engine(start, name, inline, addr, stack, prev_addr, prev_start, cntr)
        # print([ frame["inline"] for frame in stack ])
        
        # If stack has changed, we potentially need to generate a new call chain in flamegraph format
        if changed:
            trace = [ frame["inline"] for frame in stack ]
            call_chain = ";".join(trace)

            if call_chain not in flame:
                flame[call_chain] = 0

        flame[call_chain] += 1

        prev_addr = addr
        prev_start = start
        cntr += 1

        if cntr % 10000 == 0:
            print(f"Processed {cntr} instructions; flame size: {len(flame)}")

    with open(out_path, 'w') as f:
        for key in flame:
            print(f"{key} {flame[key]}", file = f)
    print("saved to ", out_path)

    return out_path

def search_for_vmlinux(trace_path: str) -> str:
    vmlinuxpath_start = trace_path + ".vmlinux"
    pattern = f"{vmlinuxpath_start}*"

    # Use glob.iglob with recursive=True to find matches in all subdirectories
    files = glob.iglob(pattern, recursive=True)
    for file in files:
        return file

    print("No vmlinux found for trace ", trace_path)
    exit(1)

def get_all_traces(folder_path: str, arch : str):
    print('folder_path', folder_path)
    benchmarks = [
        "graphbig_bfs",
        "graphbig_cc", 
        "graphbig_dc", 
        "graphbig_dfs", 
        "graphbig_pagerank", 
        "graphbig_sssp", 
        "graphbig_tc", 
        "gups",
        "sysbench",
    ]
    
    thp = [
        'never',
        'always'
    ]
    # example radix_always_graphbig_bfs_walk_log.bin

    trace_list = []
    for benchmark in benchmarks:
        for thp_policy in thp:
            pattern = f"{folder_path}/{arch}_{thp_policy}_{benchmark}_walk_log.bin"
            files = glob.glob(pattern)
            trace_list += list(files)

    run_info_list = []

    for trace in trace_list:
        vmlinux_path = search_for_vmlinux(trace)
        out_path = trace + ".kern_inst.folded"
        run_info_list.append((vmlinux_path, trace, out_path, arch))

    # print remove folder path
    print('\n'.join([f"{os.path.basename(run_info[0])} {os.path.basename(run_info[1])} {os.path.basename(run_info[2])}" for run_info in run_info_list]))
    return run_info_list

def produce_flame_graph(folded_path: str):
    flamegraph_out_path = folded_path + ".svg"
    command = f"FlameGraph/flamegraph.pl {folded_path} > {flamegraph_out_path}"
    print(command)
    subprocess.run(command, shell=True, check=True)
    print("Flamegraph saved to ", flamegraph_out_path)
    return flamegraph_out_path

def wrapper(vmlinux_path, trace_path, out_path, arch):
    # produce_flame_folded(vmlinux_path, trace_path, out_path, arch)
    high_level_path = get_high_level_distribution(out_path)
    data_folder = "kernel_inst"

    shutil.copy(out_path, os.path.join(data_folder, os.path.basename(out_path)))
    shutil.copy(high_level_path, os.path.join(data_folder, os.path.basename(high_level_path)))

    produce_flame_graph(os.path.join(data_folder, os.path.basename(out_path)))


def main():
    parser = argparse.ArgumentParser(description='An example script with arguments.')
    # single file
    parser.add_argument('--vmlinux', type=str, help='vmlinux path')
    parser.add_argument('--trace', type=str, help='binary log path')
    parser.add_argument('--out', type=str, help='output path')

    # group run
    parser.add_argument('--folder', type=str, help='folder path')
    
    parser.add_argument('--arch', type=str, help='radix or ecpt. Must choose one')
    parser.add_argument('--dry', type=bool, help='dry run')

    args = parser.parse_args()

    if args.folder != None:
        run_info_list = get_all_traces(args.folder, args.arch)
        if args.dry:
            print("Dry run done")
            exit(0)
            
        jobs = []
        for run_info in run_info_list:
            p = multiprocessing.Process(target=wrapper, args=run_info)
            jobs.append(p)
            p.start()

        for j in jobs:
            j.join()
        exit(0)

    if args.vmlinux == None:
        vmlinux_path = search_for_vmlinux(args.trace)
    else:
        vmlinux_path = args.vmlinux
    trace_path = args.trace
    out_path = args.out
    arch = args.arch

    print(vmlinux_path)

    if (vmlinux_path == None) or (trace_path == None) or (arch == None):
        print("Please provide vmlinux and binary log path and arch")
        exit(1)
    if (args.out == None):
        out_path = "flamegraph.folded"

    produce_flame_folded(vmlinux_path, trace_path, out_path, arch)
    get_high_level_distribution(out_path)

if __name__ == "__main__":
    main()
