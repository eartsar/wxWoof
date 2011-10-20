#! /usr/bin/env python

import subprocess

linkedprocess = subprocess.Popen(["arch", "-i386", "python", "window.py"], stdout = subprocess.PIPE)
outs = linkedprocess.communicate()