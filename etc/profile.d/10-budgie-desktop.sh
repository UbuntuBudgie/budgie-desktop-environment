if [[ $DESKTOP_SESSION != 'budgie-desktop' ]]
then
    return 0
fi

# First logon does lots of things - we don't need to keep repeating
# these checks since it will slow down the desktop show slightly

# keycontrol - we suffix number when keycontrol needs to be rerun
# when the package updates
if [ ! -f ~/.config/budgie-desktop/keycontrol2 ]
then
    cd /usr/share/budgie-desktop/keycontrol/; . ./gnome-custom-keybinding-setup
    mkdir -p ~/.config/budgie-desktop
    # delete old keycontrol files (if they have been previously created)
    rm -f ~/.config/budgie-desktop/keycontrol*
    touch ~/.config/budgie-desktop/keycontrol2
fi

if [ -f ~/.config/budgie-desktop/firstrun ]
then
    return 0
fi

touch ~/.config/budgie-desktop/firstrun

mkdir -p ~/.config/autostart

# caffeine
CAFF=`which caffeine`
if [ "$CAFF" ]
then
    cp /usr/share/applications/caffeine-indicator.desktop ~/.config/autostart
fi

# plank
PLK=`which plank`
if [ "$PLK" ]
then
    cp /usr/share/budgie-desktop/plank.desktop ~/.config/autostart
fi
