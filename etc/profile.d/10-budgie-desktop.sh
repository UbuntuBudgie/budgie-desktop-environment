#!/bin/sh

# force environment variable removal to allow QT apps to be themed correctly
# this is new due to zesty including QT 5.8
unset QT_STYLE_OVERRIDE
