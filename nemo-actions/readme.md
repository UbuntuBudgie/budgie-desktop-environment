# How to merge translations

What we are going to-do is take a git repo full of .po files that have the strings we want to extract
Then merge the translation strings

For budgie-desktop-grid.nemo_action


    git clone https://github.com/cinnamon4-debian/cinnamon-translations/tree/master/po-export/nemo

    cd cinnamon-translations

now copy the budgie-deskto-grid.nemo_action to the base of the cinnamon-translations folder

edit the nemo_action file and prefix _ to Name= and Comment= 

i.e.

    _Name=Align to _grid
     _Comment=Keep icons aligned to a grid

Save and exit 
run:

    intltool-merge --desktop-style ./po-export/nemo budgie-desktop-grid.nemo_action budgie-desktop-grid.nemo_action2

Edit the nemo_action2 file and global replace "nemo-" with nothing i.e. so that all the languages are without nemo-{language file}
Copy and rename the nemo_action2 file to the project nemo_actions folder

