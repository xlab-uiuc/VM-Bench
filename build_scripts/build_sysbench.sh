#!/bin/bash

# instal dependency package if needed
# apt -y install make automake libtool pkg-config libaio-dev

BASEDIR=`pwd`
cd $BASEDIR/sysbench

echo "Building sysbench..."
./autogen.sh
./configure --without-mysql
make -j `nproc`

if test -f "$BASEDIR/sysbench/src/sysbench"; then
    echo "Done building sysbench!"
else
    echo "Fail to build sysbench"
fi

