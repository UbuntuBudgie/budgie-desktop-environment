if [[ $DESKTOP_SESSION != 'budgie-desktop' ]]
then
    return 0
fi

# First logon does lots of things - we don't need to keep repeating
# these checks since it will slow down the desktop show slightly

# we have alot of applications claiming the privilege to run
# inode/directory stuff i.e. double clicking folders - we
# need to force nemo to be the default on first logon - thereafter
# the logged on user can choose whichever default they want
if [ ! -f ~/.config/budgie-desktop/mimecontrol ]
then
	mkdir -p ~/.config/budgie-desktop
	xdg-mime default nemo.desktop inode/directory
	touch ~/.config/budgie-desktop/mimecontrol
fi

# keycontrol - we suffix number when keycontrol needs to be rerun
# when the package updates
if [ ! -f ~/.config/budgie-desktop/changekeycontrol4 ]
then
	cd /usr/share/budgie-desktop/keycontrol/; python3 ./bin/change-keybinding.py; cd
	mkdir -p ~/.config/budgie-desktop
	# delete old keycontrol files (if they have been previously created)
    rm -f ~/.config/budgie-desktop/changekeycontrol*
    touch ~/.config/budgie-desktop/changekeycontrol4
fi

if [ ! -f ~/.config/budgie-desktop/keycontrol4 ]
then
    cd /usr/share/budgie-desktop/keycontrol/; . ./gnome-custom-keybinding-setup; cd
    mkdir -p ~/.config/budgie-desktop
    # delete old keycontrol files (if they have been previously created)
    rm -f ~/.config/budgie-desktop/keycontrol*
    touch ~/.config/budgie-desktop/keycontrol4
fi

if [ -f ~/.config/budgie-desktop/firstrun ]
then
    return 0
fi

touch ~/.config/budgie-desktop/firstrun

mkdir -p ~/.config/autostart

# plank
PLK=`which plank`
if [ "$PLK" ]
then
    cp /usr/share/budgie-desktop/plank.desktop ~/.config/autostart
    cp -r /usr/share/budgie-desktop/home-folder/.config ~/
fi

# templates
bash -c 'sleep 20 && /usr/share/budgie-desktop/home-folder/copytemplates' &

