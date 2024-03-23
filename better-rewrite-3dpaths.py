#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
replaces paths for 3d models in the footprints with actual 3d files when we can
find them
"""
import os
import re
import logging
from logging.handlers import RotatingFileHandler

log_file = 'rewrite-log.log'


def get_log():
    lev = 'debug'
    if not os.path.exists(log_file):
        open(log_file, 'a').close()
    log = logging.getLogger(__name__)
    if log.hasHandlers():
        log.handlers.clear()
    if lev == 'info':
        log.setLevel(logging.INFO)
    elif lev == 'debug':
        log.setLevel(logging.DEBUG)
    handler = RotatingFileHandler(log_file, mode='a',
                                  maxBytes=10240000000,
                                  encoding='utf-8')
    formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    log.addHandler(handler)
    log.info('started motion detection')
    log.info('Acquired Logger')
    return log


def get_git(log):
    mods = []
    git_root = None
    for dirname, dirnames, filenames in os.walk("./"):
        dirname = os.path.realpath(dirname)
        if ".git" in dirnames:
            # don't go into our root .git directory.
            dirnames.remove(".git")
            log.info('Dirnames less git: {}'.format(dirnames))
        elif ".git" in filenames:
            # this is the submodule root
            git_root = dirname
            for filename in filenames:
                log.info('filename: {}'.format(filename))
                is_dir = os.path.isdir(filename)
                is_mod = os.path.splitext(filename)[-1] == ".kicad_mod"
                if not is_dir and is_mod:
                    if git_root is None:
                        raise Exception("Could not find git root for {}".format(filename))
                    mod = os.path.join(dirname, filename)
                    log.info('mod is: {}'.format(mod))
                    mods.append([git_root, mod])
    log.info('Returned mods: {}'.format(mods))
    return mods, git_root


def rewrite_mods(mods, git_root, log):
    for git_root, mod in mods:
        model_paths = []
        try:
            with open(mod, "r") as f:
                text = f.read()
                new_text = text
                model_paths = re.findall(r"\(model \"?(.+?)\"?\n", text)
                log.info('model paths: {}'.format(model_paths))
                for path in model_paths:
                    model_filename = os.path.basename(path)
                    log.info('model filename: {}'.format(model_filename))
                    new_path = None
                    for dirname, dirnames, filenames in os.walk(git_root):
                        for filename in filenames:
                            if model_filename == filename:
                                new_path = os.path.join(git_root, dirname, filename)
                                new_text = new_text.replace(path, new_path)
                                break
                            if new_path is not None:
                                break
                if new_text != text:
                    print("Replacing 3d model path for {}".format(mod))
                with open(mod, "w") as f:
                    f.write(new_text)
        except Exception as e:
            print("Could not parse {}: {}".format(mod, e))


def main():
    log = get_log()
    if not os.path.exists(log_file):
        print('Log file does not exist')
        exit(1)
    mods, git_root = get_git(log)
    rewrite_mods(mods, git_root, log)


if __name__ == '__main__':
    main()
