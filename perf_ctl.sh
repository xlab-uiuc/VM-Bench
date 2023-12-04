#!/usr/bin/bash

set -x

mkfifo ctl.fifo
# exec {ctl_fd}<>ctl_fd.fifo
mkfifo ack.fifo
# exec {ctl_fd_ack}<>ctl_fd_ack.fifo
# echo ctl_fd: $ctl_fd

# echo ctrl_fd_ack: $ctl_fd_ack
# + PERF_CTL_FD=$ctl_fd PERF_CTL_ACK_FD=$ctl_fd_ack perf stat --delay=-1 --control fd:${ctl_fd},${ctl_fd_ack} -- build/prog
# ++ PERF_CTL_FD=10
# ++ PERF_CTL_ACK_FD=11

# sudo perf stat --delay=-1 --control fd:${ctl_fd} -- ./a.out $ctl_fd $ctl_fd_ack
# sudo perf stat --delay=-1 --control=fifo:ctl_fd.fifo,ack.fifo -- ./a.out
sudo perf stat -e instructions -e page-faults --delay=-1 --control=fifo:ctl.fifo,ack.fifo -- ./mem_test ctl.fifo ack.fifo
# sudo perf stat --delay=-1 --control=fifo:ctl_fd.fifo -- ./perf_ctl
# ++ perf stat --delay=-1 --control fd:10,11 -- build/prog
# sudo perf stat -- ./a.out
# sudo perf report

# -e instructions page-faults 