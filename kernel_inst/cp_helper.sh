#!/bin/bash

file_list=$(ls | grep always | grep -v postgres | grep -v redis)

for file in ${file_list[@]}; do
    if [ -f $file ]; then
        echo "Processing $file"
    fi
    mv $file thp_always_archived/
done
