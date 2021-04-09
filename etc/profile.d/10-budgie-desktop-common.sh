# Not bash ?
#[ -n "${BASH_VERSION:-}" ] || return 0

# Not an interactive shell?
#[[ $- == *i* ]] || return 0

if [[ $DESKTOP_SESSION != 'budgie-desktop' ]]
then
    return 0
fi

export QT_QPA_PLATFORMTHEME=qt5ct

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

nohup bash -c '/usr/share/budgie-desktop/launch_welcome &'
