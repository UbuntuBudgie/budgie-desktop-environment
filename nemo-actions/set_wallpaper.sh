#!/bin/bash

if [ $# -eq 0 ]
then
     echo "No arguments supplied"
     exit 1
fi

gsettings set org.gnome.desktop.background picture-uri "$1"
gsettings set org.gnome.desktop.screensaver picture-uri "$1"

exit 0
