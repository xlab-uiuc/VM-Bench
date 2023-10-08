#!/bin/bash

BASEDIR=`pwd`

# loop24 is the loop device for ~/linux_gen_ECPT/image.ext4
MOUNT_PATH=/mnt/image

sudo mount /dev/loop24 $MOUNT_PATH
sudo cp mem_test.c $MOUNT_PATH/

sudo chroot $MOUNT_PATH/ /bin/bash -c "gcc mem_test.c -no-pie -fno-PIE -o mem_test;"

sudo cp $MOUNT_PATH/mem_test $BASEDIR/

sudo umount $MOUNT_PATH