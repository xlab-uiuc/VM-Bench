#!/bin/bash

VM_LOGGING_CTL_PORT=2025

while true; do
    nc -l -p $VM_LOGGING_CTL_PORT | while read line; do
        case "$line" in
        "start")
            echo "trace logging start!"
            ./ycsb/start 
            ;;
        "end")
            echo "trace logging end!"
            ./ycsb/end 
            ;;
        *)
            echo "Unknown command received: $line"
            ;;
        esac
    done
done

exit 0