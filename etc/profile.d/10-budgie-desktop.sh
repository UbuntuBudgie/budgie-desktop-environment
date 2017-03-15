#!/bin/sh

# force QT override to not have a value to allow QT apps to be themed correctly
# this is new due to zesty including QT 5.8
export QT_STYLE_OVERRIDE=

# with qt-style-plugins ensure QT apps now pickup a GTK theme
export QT_QPA_PLATFORMTHEME=gtk2

# for the live CD ensure we override chromium-browser
# our .desktop disables gnome-keyring from displaying since
# on a live CD there is no password for gnome-keyring to get a hold of
VAL=`df | grep aufs`

if [ "$VAL" ]
then
   sudo cp /usr/share/budgie-desktop/chromium-browser.desktop /usr/share/applications
fi

