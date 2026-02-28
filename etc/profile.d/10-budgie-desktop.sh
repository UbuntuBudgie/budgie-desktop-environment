# Not bash or zsh?
#[ -n "${BASH_VERSION:-}" ] || return 0

# Not an interactive shell?
#[[ $- == *i* ]] || return 0

if [[ $DESKTOP_SESSION != 'budgie-desktop' ]]
then
    return 0
fi

# First logon does lots of things - we don't need to keep repeating
# these checks since it will slow down the desktop show slightly
if [ -f ~/.config/budgie-desktop/firstrun ]
then
    return 0
fi

touch ~/.config/budgie-desktop/firstrun

# templates
bash -c 'sleep 20 && /usr/share/budgie-desktop/home-folder/copytemplates' &
