#!/bin/bash

file_list=$(ls | grep sysbench)

for file in ${file_list[@]}; do
    if [ -f $file ]; then
        echo "Processing $file"
    fi
    cp $file ../kernel_inst_high_level/
done
