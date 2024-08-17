# Not bash ?
#[ -n "${BASH_VERSION:-}" ] || return 0

# Not an interactive shell?
#[[ $- == *i* ]] || return 0

if [[ $DESKTOP_SESSION != 'budgie-desktop' ]]
then
    return 0
fi

#export QT_QPA_PLATFORMTHEME=qt5ct

# First logon does lots of things - we don't need to keep repeating
# these checks since it will slow down the desktop show slightly

if [ -f ~/.config/budgie-desktop/firstruncommon ]
then
    return 0
fi

mkdir -p ~/.config/budgie-desktop
touch ~/.config/budgie-desktop/firstruncommon

nohup bash -c '/usr/share/budgie-desktop/launch_welcome &'
