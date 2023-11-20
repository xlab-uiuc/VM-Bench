#!/usr/bin/env bash
# See https://github.com/xlab-uiuc/LEBench/blob/master/README.md for parameter setup

cd LEBench;
COMMAND_CPU=8
rm -f test_file.txt
sudo taskset -ac $COMMAND_CPU TEST_DIR/OS_Eval 0 `uname -r`

KERNEL_NAME=`uname -r`
THP_CONFIG="no_thp_support"
thp_file="/sys/kernel/mm/transparent_hugepage/enabled"

# Check if the file exists
if [[ -f $thp_file ]]; then
    # Read the content of the file
    content=$(cat $thp_file)
    
    # Check if 'always' or 'madvise' is active (indicated by the [brackets])
    if [[ $content == *"[always]"* ]]; then
        THP_CONFIG="THP_always"
    elif [[ $content == *"[madvise]"* ]]; then
        THP_CONFIG="THP_madvise"
    elif [[ $content == *"[never]"* ]]; then
        THP_CONFIG="THP_never"
    else
        echo "Unable to determine the status of Transparent Huge Pages."
    fi
else
    echo "Transparent Huge Pages is not supported on this system."
fi

TIME=`date "+%Y-%m-%d-%H-%M-%S"`
FILE_PREFIX=${KERNEL_NAME}_${THP_CONFIG}_LEBench_${TIME}

OUT_FOLDER="../paper_results/${KERNEL_NAME}/LEBench"
mkdir -p ${OUT_FOLDER}

mv new_output_file.csv ${OUT_FOLDER}/${FILE_PREFIX}.csv
rm -f test_file.txt