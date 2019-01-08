#!/bin/bash

# following script cleans up our /etc/skel version of the Templates configuration
# this is now (and correctly) installed as part of the login sequence
# We delete only the files we initially installed.  It doesnt matter if
# someone has modified a file - we will be overwriting it anyway when the
# user logs in for the first time.

BASE="/etc/skel/Templates"
TEMPLATES=(Empty\ File
LibreOffice\ Impress.odp  
MS\ PowerPoint.pptx       
LibreOffice\ Calc.ods     
LibreOffice\ Writer.odt   
MS\ Word.docx             
LibreOffice\ Draw.odg     
MS\ Excel.xlsx            
Text\ File.txt    
)

for ((i = 0; i < ${#TEMPLATES[@]}; i++))
do
  filetoremove="$BASE/${TEMPLATES[$i]}"
  [ -f "$filetoremove" ] && rm "$filetoremove"
done

rmdir --ignore-fail-on-non-empty $BASE

