#!/bin/bash

# instal dependency package if needed
# apt -y install make automake libtool pkg-config libaio-dev

BASEDIR=`pwd`
cd $BASEDIR/graphBIG

echo "Building graphBIG..."
# Download libpfm-4.12.0
LIBPFM_SOURCE="https://sourceforge.net/projects/perfmon2/files/latest/download"
LIBPFM="libpfm-4.12.0"
cd tools
if [[ -d "$LIBPFM" ]]; then
    echo "$LIBPFM Ready."
else
    wget --output-document=$LIBPFM.tar.gz $LIBPFM_SOURCE 
    tar -xvf $LIBPFM.tar.gz
fi

# Apply libpfm version patch

if grep -q $LIBPFM Makefile ; then
    echo "Makefile version correct."
else
    cp $BASEDIR/patches/libpfm_Makefile.patch .
    git apply libpfm_Makefile.patch
fi

cd $BASEDIR/graphBIG/benchmark
make


bechmarks=(
    "./graphBIG/benchmark/bench_betweennessCentr/bc"
    "./graphBIG/benchmark/bench_BFS/bfs"
    "./graphBIG/benchmark/bench_DFS/dfs"
    "./graphBIG/benchmark/bench_degreeCentr/dc"
    "./graphBIG/benchmark/bench_shortestPath/sssp"
    "./graphBIG/benchmark/bench_connectedComp/connectedcomponent"
    "./graphBIG/benchmark/bench_triangleCount/tc"
    "./graphBIG/benchmark/bench_pageRank/pagerank")

for bench in "${bechmarks[@]}"; do
    if test -f "$BASEDIR/$bench"; then
        echo "Done building $bench"
    else
        echo "Fail to build $bench"
    fi
done

LDBC_PATH="patches/LDBC.tar.gz"
if [ ! -e "$BASEDIR/$LDBC_PATH" ]; then
    echo "Downlowding LDBC dataset"
    pip install gdown
    PATH=$PATH:~/.local/bin gdown 'https://drive.google.com/uc?export=download&id=1fuk5tadoU4oHtXUNJUusQo868vS_-dSB' -O $BASEDIR/$LDBC_PATH
fi

if [ ! -e "$BASEDIR/graphBIG/dataset/LDBC" ]; then
    echo "unzipping LDBC dataset"
    tar -xf $BASEDIR/$LDBC_PATH --directory $BASEDIR/graphBIG/dataset/
fi


if [ ! -e "$BASEDIR/graphBIG/dataset/LDBC" ]; then
    echo "LDBC dataset ready"
else
    echo "LDBC not ready. Please check before running benchmark"
fi

# tar -xf $BASEDIR/$LDBC_PATH --directory $BASEDIR/graphBIG/dataset/

# if test -f "$BASEDIR/$LDBC_PATH"; then
#     tar -xf $BASEDIR/$LDBC_PATH --directory $BASEDIR/graphBIG/dataset/
# else
#     echo "Please download LDBC dataset to patches/LDBC.tar.gz"
# fi