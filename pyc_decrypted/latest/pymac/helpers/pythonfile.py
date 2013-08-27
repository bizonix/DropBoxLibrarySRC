#Embedded file name: pymac/helpers/pythonfile.py
from __future__ import absolute_import
from ..dlls import libc, PythonAPI
from ..types import close_FILE_func_t

def _fclose(f):
    return libc.fclose(f)


py_fclose = close_FILE_func_t(_fclose)

def FILE_to_python_file(fp, name, mode):
    return PythonAPI.PyFile_FromFile(fp, name, mode, py_fclose)


def exchangedata(src, dest):
    src = src.encode('utf8')
    dest = dest.encode('utf8')
    libc.exchangedata(src, dest, 0)
