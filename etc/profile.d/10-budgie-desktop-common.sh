if [[ $DESKTOP_SESSION != 'budgie-desktop' ]]
then
    return 0
fi

# force QT override to not have a value to allow QT apps to be themed correctly
# this is new due to zesty including QT 5.8
export QT_STYLE_OVERRIDE=

# with qt-style-plugins ensure QT apps now pickup a GTK+2 theme
# N.B. we don't have in Ubuntu a gtk3 based override yet.
export QT_QPA_PLATFORMTHEME=gtk2

# First logon does lots of things - we don't need to keep repeating
# these checks since it will slow down the desktop show slightly

if [ -f ~/.config/budgie-desktop/firstruncommon ]
then
    return 0
fi

mkdir -p ~/.config/budgie-desktop
touch ~/.config/budgie-desktop/firstruncommon

# Tilix needs to include a bash statement to source vte otherwise an error dialog
# is displayed and proper folder navigation when creating new tiled windows is
# not available.  Since Ubuntu's bash.bashrc does NOT execute shell scripts as per
# Fedora, we'll have to mimic this via the login shell execution of this script.

# be safe - if TILIX_ID already exists in .bashrc lets assume
# either we have already done this via another run or
# another package has made similar changes in this area

if ! grep -q "TILIX_ID" ~/.bashrc; then
    # lets delete 17.04 Terminix that was added
    sed -i.bak '/# Ubuntu Budgie END$/d' ~/.bashrc
    rm -f ~/.bashrc.bak

    # now append vte source
    cat /usr/share/budgie-desktop/vteprompt.txt >> ~/.bashrc
fi

mkdir -p ~/.config/autostart

# welcome - give welcome an autostart if its not copied on first initialisation
if [ -f /snap/ubuntu-budgie-welcome/current/usr/bin/budgie-welcome ] && [ ! -f ~/.config/autostart/budgie-welcome.desktop ]
then
    cp /usr/share/budgie-desktop/budgie-welcome.desktop ~/.config/autostart
fi
