#!/bin/bash

# instal dependency package if needed
# apt -y install make automake libtool pkg-config libaio-dev

BASEDIR=`pwd`

cd $BASEDIR/biobench2
cp ../patches/buildMUMmer.sh .

sh buildMUMmer.sh

cp $BASEDIR/patches/runMUMmer.pl .

if test -f "$BASEDIR/biobench2/MUMmer/mummer"; then
    echo "Done building mummer!"
else
    echo "Fail to build mummer:("
fi