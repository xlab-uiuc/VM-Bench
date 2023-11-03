CPUPOWER_PATH="/home/siyuan/linux_5.15_vanilla/tools/power/cpupower"

sudo LD_LIBRARY_PATH=$CPUPOWER_PATH $CPUPOWER_PATH/cpupower --cpu all frequency-set --governor ondemand