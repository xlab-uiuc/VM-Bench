#!/usr/bin/env bash

for file in `ls *_out_kernel.folded`; do
	echo "$file"
	/home/jz/vm-interface/rethinkVM_bench/FlameGraph/flamegraph.pl "$file" > "$file.svg"
done