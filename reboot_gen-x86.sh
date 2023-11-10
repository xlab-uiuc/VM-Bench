#!/bin/bash

# get menuentry from 
# awk -F\' '/menuentry / {print $2}' /boot/grub/grub.cfg
# source https://adamtheautomator.com/ubuntu-grub

sudo grub-reboot "Advanced options for Ubuntu>Ubuntu, with Linux 5.15.0-gen-x86"
sudo reboot
