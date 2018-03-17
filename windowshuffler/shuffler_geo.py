#!/usr/bin/env python3
import subprocess

import gi

gi.require_version("Wnck", "3.0")
from gi.repository import Wnck, Gdk

"""
WindowShuffler
Author: Jacob Vlijm
Copyright © 2017-2018 Ubuntu Budgie Developers
Website=https://ubuntubudgie.org
This program is free software: you can redistribute it and/or modify it under
the terms of the GNU General Public License as published by the Free Software
Foundation, either version 3 of the License, or any later version. This
program is distributed in the hope that it will be useful, but WITHOUT ANY
WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR
A PARTICULAR PURPOSE. See the GNU General Public License for more details. You
should have received a copy of the GNU General Public License along with this
program.  If not, see <https://www.gnu.org/licenses/>.
"""


def mousepos():
    # find out mouse location
    return Gdk.get_default_root_window().get_pointer()[1:3]


def check_win_name(win):
    # certain windows should be ignored
    return win.get_name() not in [
        "WindowMatrix", "Usage & general shortcuts"
    ]


def get_currmonitor_atpos(x, y, display=None):
    """
    fetch the current monitor (obj) at position. display is optional to save
    fuel if it is already fetched elsewhere
    """
    if not display:
        display = Gdk.Display.get_default()
    display = Gdk.Display.get_default()
    return display.get_monitor_at_point(x, y)


def get_winlist(scr=None, selecttype=None):
    """
    get the window list. possible args: screen, select_type, in case it is
    already fetched elsewhere. select type is optional, to fetch only
    specific window types.
    """
    if not scr:
        scr = Wnck.Screen.get_default()
        scr.force_update()
    windows = scr.get_windows()
    if selecttype:
        windows = [w for w in windows if check_windowtype(w, selecttype)]
    return windows


def get_strut(xid):
    """
    get the strut- values from xprop, on dock type windows. Since Plank is
    an exception, the function indicates if the dock is a plank instance.
    """
    s = "_NET_WM_STRUT(CARDINAL) = "
    strut_data = subprocess.check_output(
        ["xprop", "-id", xid]
    ).decode("utf-8")
    match = [int(n) for n in [
        l for l in strut_data.splitlines() if s in l
    ][0].split("=")[1].strip().split(",")
             ]
    plank = True if 'WM_NAME(STRING) = "plank"' in strut_data else False
    return match


def get_plankstrutvals(span, strutvals, mpos):
    """
    since the set strut- values plank returns seem incorrect, we need to fix
    it for multi-monitor situations.
    """
    # get left_strutval - ok
    left = strutvals[0]
    left = left if left == 0 else left - mpos[0]
    # get right strutval
    right = strutvals[1]
    right = right if right == 0 else right - (span[0] - (mpos[0] + mpos[2]))
    # get top strutval
    top = strutvals[2]
    top = top if top == 0 else top - mpos[1]
    # get bottom strutval
    bottom = strutvals[3]
    # print("research", bottom, mpos[1], mpos[3])
    bottom = bottom if bottom == 0 else \
        bottom - (span[1] - (mpos[1] + mpos[3]))
    return left, right, top, bottom


def get_windows_oncurrent(scr=None):
    """
    returns all visible, non- minimized windows on current workspace, monitor
    position and working area
    """
    # get screen / span size for if plank is on the right
    if not scr:
        scr = Wnck.Screen.get_default()
        scr.force_update()
    screensize = scr.get_width(), scr.get_height()
    # get all windows
    relevants = get_winlist(scr, None)
    mp = mousepos()
    currmonitor = get_currmonitor_atpos(mp[0], mp[1])
    planks = []
    otherdocks = []
    normal = []
    # split them up
    for w in relevants:
        loc = w.get_geometry()[:2]
        monitor = get_currmonitor_atpos(loc[0], loc[1])
        if monitor == currmonitor:
            typedata = str(w.get_window_type())
            if "NORMAL" in typedata:
                if check_win_name(w):
                    normal.append(w)
            elif "DOCK" in typedata:
                if w.get_name() == "plank":
                    planks.append(w)
                else:
                    otherdocks.append(w)
    # current monitor position and -size
    mgeo = currmonitor.get_geometry()
    mpos = [mgeo.x, mgeo.y, mgeo.width, mgeo.height]
    # get data on docks on current screen
    dockgeo = [get_strut(str(d.get_xid())) for d in otherdocks]
    plankgeo = [
        get_plankstrutvals(
            screensize, get_strut(str(p.get_xid())), mpos,
        ) for p in planks
    ]
    allpanels = dockgeo + plankgeo
    strut = [sum([strut[i] for strut in allpanels]) for i in range(4)]
    # summarize
    # working area
    wa = [
        strut[0], strut[2], mpos[2] - (strut[0] + strut[1]),
                            mpos[3] - (strut[2] + strut[3]),
    ]
    # normal, visible windows on current monitor on current workspace
    currws = scr.get_active_workspace()
    windows = [
        w for w in normal if all([
            w.get_workspace() == currws,
            not w.is_minimized(),
        ])
    ]
    # offset due to monitor position
    offset = mpos[0], mpos[1]
    return {"wa": wa, "windows": windows, "offset": offset}
