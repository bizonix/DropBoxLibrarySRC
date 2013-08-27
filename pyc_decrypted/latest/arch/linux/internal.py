#Embedded file name: arch/linux/internal.py
from __future__ import absolute_import
import os
import sys
import errno
import subprocess32 as subprocess
import tempfile
import build_number
from build_number import BUILD_KEY
from dropbox.features import current_feature_args
from dropbox.trace import TRACE, unhandled_exc_handler

def executable(opts = ()):
    opts = list(opts) + current_feature_args()
    if hasattr(build_number, 'frozen'):
        ex = sys.executable
        cmd = [ex] + list(opts)
    else:
        cmd = [sys.executable, os.path.join('bin', 'dropbox')] + list(opts) + ['--key=%s' % BUILD_KEY]
    return cmd


def get_contents_root():
    if hasattr(build_number, 'frozen'):
        executable = sys.executable.decode('utf8')
        return os.path.split(executable)[0]
    else:
        return os.getcwdu()


def run_program(cmd, input = None):
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIPE)
    stdout, stderr = proc.communicate(input)
    if proc.returncode != 0:
        TRACE('command line was %r' % (cmd,))
        TRACE('stdout: %s' % stdout)
        TRACE('stderr: %s' % stderr)
        raise Exception('Failed to run command (%r)' % proc.returncode)
    return proc.returncode


def file_system_string(obj):
    if not isinstance(obj, str):
        if isinstance(obj, unicode):
            try:
                obj = obj.encode(sys.getfilesystemencoding())
            except UnicodeEncodeError:
                obj = obj.encode('utf8', 'ignore')

        else:
            obj = str(obj)
    return obj


def run_as_root(cmd_list, desc = ''):
    desc = file_system_string(desc)
    cmd_list = map(file_system_string, cmd_list)
    programs = (['gksu',
      '-m',
      desc,
      '--'], ['kdesu', '-c'], ['beesu'])
    for p in programs:
        try:
            return run_program(p + cmd_list)
        except OSError as e:
            if e.errno == errno.ENOENT:
                continue
            else:
                raise

    with tempfile.NamedTemporaryFile() as tmp:
        script = '#!/bin/bash\nsudo -K\nzenity --entry --title="Dropbox" --text="%s" --entry-text "" --hide-text | sudo -S %s\nif [ "$?" != 0 ]; then\nzenity --error --text="Sorry, wrong password"\nexit 1\nfi\n\n# End' % (desc, ' '.join(cmd_list))
        tmp.write(script)
        tmp.flush()
        return run_program(['bash', tmp.name])
