#!/bin/bash

# instal dependency package if needed
# apt -y install make automake libtool pkg-config libaio-dev

BASEDIR=`pwd`

echo "Building mem_test..."

gcc mem_test.c -no-pie -fno-PIE -o mem_test 

if test -f "$BASEDIR/mem_test"; then
    echo "Done building mem_test!"
else
    echo "Fail to build mem_test"
fi

