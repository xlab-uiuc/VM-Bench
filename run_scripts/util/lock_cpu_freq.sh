#!/bin/bash

# borrowed from Yan Sun

CPUPOWER_PATH="/home/siyuan/linux_5.15_vanilla/tools/power/cpupower"
sudo LD_LIBRARY_PATH=$CPUPOWER_PATH $CPUPOWER_PATH/cpupower --cpu all frequency-set --freq 3000MHz
# sudo sh -c 'echo 0 > /sys/devices/system/cpu/cpufreq/boost'

# Just for easy copy
# sudo cpupower --cpu all frequency-set --governor ondemand
