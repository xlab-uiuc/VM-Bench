#!/usr/bin/env bash

BASEDIR=`pwd`
cd $BASEDIR
./run_scripts/gups.sh
./run_scripts/mummer.sh
./run_scripts/sysbench.sh
