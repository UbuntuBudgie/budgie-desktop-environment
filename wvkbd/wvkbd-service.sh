#!/bin/bash

KEYBOARD_BIN="wvkbd-mobintl"

SCRIPT_NAME=$(basename "$0")
if [ $(pgrep -f "$SCRIPT_NAME" | wc -l) -gt 2 ]; then
    exit 0
fi

# Ensure exactly ONE hidden keyboard process exists on startup
if ! pgrep -x "$KEYBOARD_BIN" > /dev/null; then
    $KEYBOARD_BIN -l full --hidden &
    # Allow the layer surface a fraction of a second to initialize hidden
    sleep 0.2
fi

# Monitor GSettings and target the binary globally via pkill signals
gsettings monitor org.gnome.desktop.a11y.applications screen-keyboard-enabled | while read -r line; do
    if echo "$line" | grep -q "true"; then
        # SIGUSR2 instructs ALL instances of wvkbd to unhide
        pkill -SIGUSR2 -x "$KEYBOARD_BIN"
    elif echo "$line" | grep -q "false"; then
        # SIGUSR1 instructs ALL instances of wvkbd to hide
        pkill -SIGUSR1 -x "$KEYBOARD_BIN"
    fi
done
