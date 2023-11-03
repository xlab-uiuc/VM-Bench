#!/bin/bash

# borrowed from Yan Sun


CPUPOWER_PATH="/home/siyuan/linux_5.15_vanilla/tools/power/cpupower"

# echo $LD_LIBRARY_PATH
sudo LD_LIBRARY_PATH=$CPUPOWER_PATH $CPUPOWER_PATH/cpupower --cpu all frequency-info | grep "current CPU frequency"