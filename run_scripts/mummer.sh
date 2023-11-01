#!/usr/bin/env bash

(cd ./biobench2; ./runMUMmer.pl;)
# (cd ./biobench2; ./MUMmer/mummer -b -c ./MUMmer/mummer -b -c  ./MUMmer/input/hs_chrY.fa ./MUMmer/input/hs_chr17.fa  1> ./QuEST/output/results.txt 2>> benchResults.txt )