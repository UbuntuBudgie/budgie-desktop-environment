#!/bin/bash

if [ $# -eq 0 ]
then
     echo "No arguments supplied"
     exit 1
fi

if [ ! -f $1 ]
then
    echo "File $1 does not exist"
    exit 1
fi

gsettings set org.gnome.desktop.background picture-uri "file://$1"
gsettings set org.gnome.desktop.screensaver picture-uri "file://$1"

exit 0
