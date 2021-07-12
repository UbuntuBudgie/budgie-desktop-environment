#!/bin/bash

isgdm=`grep gdm3 /etc/X11/default-display-manager | wc -l`

if [ $isgdm == '1' ]; then
	notify-send -t 10000 -c INFORMATION "Screen lock" "Screen lock may not work.\nScreen lock will only work with\nlightdm"
fi

exit 0
