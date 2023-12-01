#!/bin/bash
set -x

if [ $# -ne 1 ]; then
    echo "Usage: $0 <filename>"
    exit 1
fi

FILE_NAME="$1"  # Use the first argument as the filename


BASEDIR=$(pwd)
MOUNT_PATH="/mnt/image"
BIN_NAME=$(basename "$FILE_NAME" | cut -f 1 -d '.')

# use -o loop to mount a file as a block device
# avoid setting up a loop device manually
sudo mount -o loop ../image.ext4 "$MOUNT_PATH"

# This is because the mounted image was corrupted.
# Fixed with e2fsck
# sleep 5
# sync

sudo cp "$FILE_NAME" "$MOUNT_PATH/"

sudo chroot "$MOUNT_PATH/" /bin/bash -c "gcc $FILE_NAME -no-pie -fno-PIE -o $BIN_NAME;"

sudo cp "$MOUNT_PATH/$BIN_NAME" "$BASEDIR/"

sudo umount "$MOUNT_PATH"



