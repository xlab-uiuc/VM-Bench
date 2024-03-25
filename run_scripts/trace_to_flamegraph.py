#!/usr/bin/env python3

import bisect
import collections
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

	with open(bin_log_file, 'rb') as file:
		while True:
			chunk = file.read(entry_size)  # Read in 1024-byte chunks
			if not chunk:
				break  # If the chunk is empty, end of file has been reached
			full_parsed_data = struct.unpack(entry_format, chunk)
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

def lookup_symbol(sym_addrs, sym_names, addr) -> str:
	index = bisect.bisect_right(sym_addrs, addr)

	if index:
		return (sym_addrs[index - 1], sym_names[index - 1])

	return (0x0, "__UNKNOWN_SYMBOL__")

def stack_engine(start: int, name: str, addr: int, stack: list, prev_addr: int, prev_start: int, cntr: int):
	# Not empty and in the same symbol (sequential execution), return
	if len(stack) >= 1 and prev_start == start:
		return (stack, False)

	# First instruction, must be a function enter
	if addr == start:
		stack.append({
			"ret": prev_addr,
			"start": start,
			"sym": name,
		})
		return (stack, True)

	# May be a jump enter or leave
	for idx, rets in enumerate(reversed(stack)):
		# Get the real index from reversed index
		idx = -(idx + 1)

		# Within one insn after call, assume a return
		if (addr >= rets["ret"]) and (addr <= rets["ret"] + max_insn_bytes):
			stack = stack[0 : idx]
			return (stack, True)
		# TODO: Probably we can detect jump enter near call?

	# Definitely not a return, warn and continue
	print(f"WARNING: at RIP {hex(addr)} ({hex(start)}:{name}+{hex(addr - start)}) RET {hex(prev_addr)} INSN# {hex(cntr)}: jump into the body of function")
	stack.append({
		"ret": prev_addr,
		"start": start,
		"sym": name,
	})
	return (stack, True)

def main():
	parser = argparse.ArgumentParser(description='An example script with arguments.')
	parser.add_argument('--vmlinux', type=str, help='vmlinux path')
	parser.add_argument('--trace', type=str, help='binary log path')
	parser.add_argument('--out', type=str, help='output path')
	parser.add_argument('--arch', type=str, help='radix or ecpt. Must choose one')
	args = parser.parse_args()

	vmlinux_path = args.vmlinux
	trace_path = args.trace
	out_path = args.out
	arch = args.arch

	if (vmlinux_path == None) or (trace_path == None) or (arch == None):
		print("Please provide vmlinux and binary log path and arch")
		exit(1)

	if (args.out == None):
		out_path = "flamegraph.folded"

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

	for addr in get_next_insn(trace_path, arch):
		if addr == USER_PROGRAM_MAGIC:
			# user program execution now, clears kernel stack
			stack = []
			prev_addr = 0x0
			prev_start = 0x0
			call_chain = ""
			continue

		(start, name) = lookup_symbol(sym_addrs, sym_names, addr)
		# print(f"{hex(start)} {hex(addr)} {name}")
		
		(stack, changed) = stack_engine(start, name, addr, stack, prev_addr, prev_start, cntr)
		# print([ frame["sym"] for frame in stack ])
		
		# If stack has changed, we potentially need to generate a new call chain in flamegraph format
		if changed:
			trace = [ frame["sym"] for frame in stack ]
			call_chain = ";".join(trace)

			if call_chain not in flame:
				flame[call_chain] = 0

		flame[call_chain] += 1

		prev_addr = addr
		prev_start = start
		cntr += 1

		if cntr % 100000 == 0:
			print(f"Processed {cntr} instructions; flame size: {len(flame)}")

	with open(out_path, 'w') as f:
		for key in flame:
			print(f"{key} {flame[key]}", file = f)

	print("saved to ", out_path)
if __name__ == "__main__":
	main()
