#!/bin/bash
set -x

if [ $# -ne 2 ]; then
    echo "Usage: $0 <filename> <loop_device>"
    exit 1
fi

FILE_NAME="$1"  # Use the first argument as the filename
LOOP_DEV="$2"   # Use the second argument as the loop device


BASEDIR=$(pwd)
MOUNT_PATH="/mnt/image"
BIN_NAME=$(basename "$FILE_NAME" | cut -f 1 -d '.')

sudo mount "$LOOP_DEV" "$MOUNT_PATH"
# WAIT FOR FS SYNCING ? 
sleep 5

sudo cp "$FILE_NAME" "$MOUNT_PATH/"

sudo chroot "$MOUNT_PATH/" /bin/bash -c "gcc $FILE_NAME -no-pie -fno-PIE -o $BIN_NAME;"

sudo cp "$MOUNT_PATH/$BIN_NAME" "$BASEDIR/"

sudo umount "$MOUNT_PATH"



