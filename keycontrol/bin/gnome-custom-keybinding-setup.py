#!/usr/bin/python3 -tt
# -*- coding: utf-8 -*-

__author__    = 'Bernard Gray'
__copyright__ = '(C) 2018 Bernard Gray <bernard.gray@gmail.com>'
__license__   = 'GPLv2 or any later version'

from subprocess import *

import argparse 
import ast
import configparser
import os
import tempfile

# possible suggestion for providing system key location, which we can override
#BUDGIE_KEYS = '/usr/share/budgie/custom-keys.d/

KEY_LOC = '/org/gnome/settings-daemon/plugins/media-keys/'

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
                print('DEBUG: skipping %s, doesnt end in .dconf' % f)
    return _file_list

def loadDconf(dconf_file):
    '''write a key file into the dconf database'''
    if args.dry_run:
        print ('INFO: --dry-run active - not loading into dconf database, generated config follows')
        print ('==============================================================================')
        try:
            cmd = Popen(['cat', dconf_file], close_fds=True)
        except:
            print('ERROR: problem executing command: %s' % ' '.join(cmd))
            raise BudgieKeyError
    else:
        try:
            print("INFO: live run, writing from %s" % dconf_file)
            cmd = Popen(['cat', dconf_file], stdout=PIPE)
            cmd_pipe = Popen(['dconf', 'load', KEY_LOC], stdin = cmd.stdout, stdout = PIPE)
            cmd.stdout.close()
            cout = cmd_pipe.communicate()[0]
        except:
            print('ERROR: problem executing command: %s' % ' '.join(cmd_pipe))
            raise BudgieKeyError

if __name__ == '__main__':
    aparse = argparse.ArgumentParser(description = "load custom keybindings via dconf keys")
    aparse.add_argument(
            '-r', '--dry-run', action = 'store_true', 
            help = 'do all operations *except* write to dconf'
    )
    aparse.add_argument(
            '-f', '--force',  action = 'store_true', 
            help = 'overwrite existing key values'
    )
    group = aparse.add_mutually_exclusive_group(required=True)
    group.add_argument(
            '-d', '--dconf-file', 
	    help = 'single dconf file to process'
    )
    group.add_argument(
            '-D', '--dconf-dir', 
	    help = 'directory of dconf custom-keybinding files to process'
    )
    args = aparse.parse_args()

    # identify the files we want to parse
    if args.dconf_file:
        dconf_files = [ os.path.abspath(args.dconf_file) ]
    else:
        dconf_files = getKeyFiles(args.dconf_dir)

    if len(dconf_files) == 0:
        print('WARNING: no files found to process')
        quit()

    # get our current dconf custom keybinding config for comparison
    curr_conf = parseDconf(check_output(['dconf', 'dump', '/org/gnome/settings-daemon/plugins/media-keys/']).decode('ascii'), True)

    # prepare a single conf object to compile all our new keys into
    out_conf = configparser.ConfigParser(interpolation=None)
    key_ref = []

    # parse all the custom keys in our conf files, and create our dconf entries from them
    for dconf_file in dconf_files:
        try:
            dconf_key = parseDconf(dconf_file)
        except configparser.MissingSectionHeaderError:
            print('ERROR: %s is missing a Section Header' % dconf_file)
        except configparser.ParsingError:
            print('ERROR: %s has an incorrectly formatted (or missing) element in section %s' % (dconf_file,key_name))
        # todo check if the key-combination is in use with some other keybinding
        # we can handle having multiple keys defined per file
        process_file = True
        for key_name in dconf_key:
            if key_name != 'DEFAULT':
                if keyNameExists(key_name, curr_conf) and key_name != '/':
                    print('INFO: dconf already has key %s' % (key_name))
                    if not args.force:
                        process_file = False
                elif key_name != '/':
                    # ugly, but if we don't check for trailing / it crashes our DE
                    if key_name.endswith('/'):
                        key_ref.append(KEY_LOC + key_name)
                    else:
                        key_ref.append(KEY_LOC + key_name + '/')
        if process_file:
            out_conf.read(dconf_file)
        else:
            print('INFO: NOT processing %s, keys already exist in dconf' % (dconf_file))

    # assemble our custom-keybindings array option, pop it into a tempfile for dconf load
    if len(key_ref) > 0:
        # get custom-bindings ref from curr_conf
        try:
            curr_key_ref = ast.literal_eval(curr_conf.get('/', 'custom-keybindings'))
            key_ref = curr_key_ref + key_ref
        except:
            pass
        # build the root section with our new custom-keybindings references
        try:
            out_conf.add_section('/')
        except configparser.DuplicateSectionError:
            pass
        out_conf.set('/', 'custom-keybindings', str(key_ref))
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as configfile:
            out_conf.write(configfile)
        # money shot
        loadDconf(configfile.name)
        if not args.dry_run:
            print('SUCCESS: config loaded, you can confirm with:')
            print('  dconf dump %s' % KEY_LOC)
    else:
        print('WARNING: nothing to do!')
