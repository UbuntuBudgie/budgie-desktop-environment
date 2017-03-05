#!/bin/sh

# force QT override to not have a value to allow QT apps to be themed correctly
# this is new due to zesty including QT 5.8
export QT_STYLE_OVERRIDE=

# with qt-style-plugins ensure QT apps now pickup a GTK theme
export QT_QPA_PLATFORMTHEME=gtk2
