#!/usr/bin/env bash


FOLDER="./run_scripts/simulation/"
STAGE=2
${FOLDER}/graphbig_bfs.sh ${STAGE}
${FOLDER}/graphbig_cc.sh ${STAGE}
${FOLDER}/graphbig_dc.sh ${STAGE}
${FOLDER}/graphbig_dfs.sh ${STAGE}
${FOLDER}/graphbig_pagerank.sh ${STAGE}
${FOLDER}/graphbig_sssp.sh ${STAGE}
${FOLDER}/graphbig_tc.sh ${STAGE}