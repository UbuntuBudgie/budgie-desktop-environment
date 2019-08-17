#!/usr/bin/python3 -tt
# -*- coding: utf-8 -*-

__license__   = 'GPLv2 or any later version'

from subprocess import *

import argparse 
import ast
import configparser
import logging as log
import os
import sys
import tempfile
import subprocess
from gi.repository import Gio

SYS_KEYS = '/usr/share/budgie-desktop/keycontrol/remove-keys/'
DCONF_KEY_PATH = '/org/gnome/settings-daemon/plugins/media-keys/'

class BudgieKeyError(Exception):
    '''A generic error handler that does nothing.'''
    pass


def parseDconf(conf, is_string=False):
    _cparse = configparser.ConfigParser(interpolation=None)
    if is_string == True:
        _cparse.read_string(conf)
    else:
        _cparse.read(conf)
    return _cparse

def keyNameExists(key, conf):
    if key != 'DEFAULT':
       try:
           exists = conf[key]
           return True
       except KeyError:
           return False

def getKeyFiles(key_dir):
    '''return a list of filenames from a given directory, 
       conforming to our key filenaming standard (*.dconf)'''
    _file_list = []
    for dirpath,_,filenames in os.walk(key_dir):
        for f in filenames:
            if f.endswith('.dconf'):
                _full_path = os.path.abspath(os.path.join(dirpath, f))
                _file_list.append(os.path.abspath(os.path.join(dirpath, f)))
            else:
                log.debug('skipping %s, doesnt end in .dconf' % f)
    return _file_list

if __name__ == '__main__':
    aparse = argparse.ArgumentParser(description = "load custom keybindings via dconf keys")
    aparse.add_argument(
            '-v', '--verbose',  action = 'store_true', 
            help = 'increased output and informational/error messages'
    )
    aparse.add_argument(
            '-D', '--dconf-dir', default=SYS_KEYS,
	    help = 'directory of dconf custom-keybinding files to process'
    )
    args = aparse.parse_args()

    # setup logging
    if args.verbose:
        log.basicConfig(level='DEBUG', format='%(levelname)s: %(message)s')
    else:
        log.basicConfig(level='INFO', format='%(levelname)s: %(message)s')

    
    dconf_files = getKeyFiles(args.dconf_dir)

    if len(dconf_files) == 0:
        log.warning('no files found to process in (' + str(args.dconf_dir) + ', ' + str(args.dconf_file) + ')')
        quit()

    # get our current dconf custom keybinding config for comparison
    curr_conf = parseDconf(check_output(['dconf', 'dump', '/org/gnome/settings-daemon/plugins/media-keys/']).decode('ascii'), True)

    # prepare a single conf object to compile all our new keys into
    out_conf = configparser.ConfigParser(interpolation=None)
    key_ref = []

    # parse all the custom keys in our conf files, and create our dconf entries from them
    settings = Gio.Settings.new('org.gnome.settings-daemon.plugins.media-keys')
    list = settings.get_strv('custom-keybindings')
    
    for dconf_file in dconf_files:
        try:
            dconf_key = parseDconf(dconf_file)
        except configparser.MissingSectionHeaderError:
            log.error('%s is missing a Section Header' % dconf_file)
        except configparser.ParsingError:
            log.error('%s has an incorrectly formatted (or missing) element in section %s' % (dconf_file,key_name))
        
        for key_name in dconf_key:
            if key_name != 'DEFAULT':
                if keyNameExists(key_name, curr_conf) and key_name != '/':
                    key_name = key_name.split('/')[1]
                    log.debug('dconf has key %s' % (key_name))
    
                    settings_args = ['gsettings',
                                     'reset-recursively',
                                     'org.gnome.settings-daemon.plugins.media-keys.custom-keybinding:/org/gnome/settings-daemon/plugins/media-keys/custom-keybindings/'+key_name+'/']
                    subprocess.run(settings_args)

                    list.remove('/org/gnome/settings-daemon/plugins/media-keys/custom-keybindings/'+key_name+'/')


    settings.set_strv('custom-keybindings', list)
