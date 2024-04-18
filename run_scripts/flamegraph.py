#!/usr/bin/env python3

import bisect
import collections
import typing

sym_addrs = []
sym_names = []
max_insn_bytes = 15 # by intel

def get_symbol_table() -> dict:
	"""TODO: @Siyuan, extract nm output into a dict as below"""

	sym_table = {
		0x3000: "test3",
		0x1000: "test1",
		0x2000: "test2",
		0x4000: "test4",
	}

	return sym_table

def get_next_insn() -> int:
	"""TODO: @Siyuan, get the address of the next instruction"""

	op_list = [
		0x1000, # test1 1
		0x1007, # test1 2
		0x1008, # test1 3
		0x1054, # test1 4
		0x1056, # test1 5
		0x3000, # test1;test3 1
		0x300c, # test1;test3 2
		0x300e, # test1;test3 3
		0x3fff, # test1;test3 4
		0x4000, # test1;test3;test4 1
		0x4005, # test1;test3;test4 2
		0x4006, # test1;test3;test4 3
		0x1060, # test1 6
		0x1062, # test1 7
		0x4000, # test1;test4 1
		0x4005, # test1;test4 2
		0x4006, # test1;test4 3
		0x1070, # test1 8
		0x1000, # test1 9
		0x1007, # test1 10
	]

	for op in op_list:
		yield op

def build_symbol_lookup(sym_table: dict) -> None:
	global sym_addrs
	global sym_names

	sym_lookup = collections.OrderedDict(sorted(sym_table.items()))
	sym_addrs = list(sym_lookup.keys())
	sym_names = list(sym_lookup.items())

def lookup_symbol(addr: int) -> str:
	index = bisect.bisect_right(sym_addrs, addr)

	if index:
		return sym_names[index - 1]

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
	build_symbol_lookup(get_symbol_table())

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

	for addr in get_next_insn():
		(start, name) = lookup_symbol(addr)

		(stack, changed) = stack_engine(start, name, addr, stack, prev_addr, prev_start, cntr)

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
	
	for key in flame:
		print(f"{key} {flame[key]}")

if __name__ == "__main__":
	main()