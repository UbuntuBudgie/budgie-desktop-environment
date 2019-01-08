#!/bin/bash

# following script cleans up our /etc/skel version of the plank configuration
# this is now (and correctly) installed as part of the login sequence
# We delete only the files we initially installed.  It doesnt matter if
# someone has modified a file - we will be overwriting it anyway when the
# user logs in for the first time.

BASE="/etc/skel/.config/plank"
SUBDIR="/dock1/launchers"
TEMPLATES=(budgie-welcome.dockitem         
libreoffice-calc.dockitem       
org.gnome.Software.dockitem
chromium-browser.dockitem
firefox.dockitem       
libreoffice-writer.dockitem     
rhythmbox.dockitem
com.gexperts.Terminix.dockitem  
nautilus.dockitem               
com.gexperts.Tilix.dockitem     
org.gnome.Nautilus.dockitem    
)

for ((i = 0; i < ${#TEMPLATES[@]}; i++))
do
  filetoremove="$BASE/$SUBDIR/${TEMPLATES[$i]}"
  [ -f "$filetoremove" ] && rm "$filetoremove"
done

find "$BASE" -type d -empty -delete
