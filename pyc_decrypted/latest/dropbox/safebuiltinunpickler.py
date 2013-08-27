#Embedded file name: dropbox/safebuiltinunpickler.py
from __future__ import absolute_import
import cPickle
import StringIO
import sys

class SafeBuiltInUnpickler(object):

    @classmethod
    def find_class(cls, module, name):
        raise cPickle.UnpicklingError('Attempting to unpickle non-built-in module %s : class %s' % (module, name))

    @classmethod
    def loads(cls, pickle_string):
        return cls.load(StringIO.StringIO(pickle_string))

    @classmethod
    def load(cls, pickle_file):
        pickle_obj = cPickle.Unpickler(pickle_file)
        pickle_obj.find_global = cls.find_class
        return pickle_obj.load()
