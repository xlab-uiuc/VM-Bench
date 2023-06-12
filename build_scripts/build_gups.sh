#!/bin/bash

# instal dependency package if needed
# apt -y install make automake libtool pkg-config libaio-dev

BASEDIR=`pwd`
cd $BASEDIR/gups

if which mpicc; then
    echo "mpicc ready."
else
    # if you don't have openmpi library installed
    sudo apt install libhdf5-mpich-dev
fi

# apply patch to add include path of mpich
if ! grep "CCFLAGS = *mpich" Makefile.linux; then
    cp $BASEDIR/patches/gups_makefile.patch .
    git apply gups_makefile.patch
fi

make -f Makefile.linux gups_vanilla;

if test -f "$BASEDIR/gups/gups_vanilla"; then
    echo "Done building gups!"
else
    echo "Fail to build gups"
fi