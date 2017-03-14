#!/usr/bin/env python3

# valid name for table and columns
import re

# allow empty name
#nameRe=re.compile(r'^([\w_]?|[\w_][\w_\d]*)$')
# illegal character in name
illegChar=re.compile(r'[-+,.|*]')
def checkName(name):
    if type(name)==list or type(name)==tuple:
        for n in name:
            checkName(n)
    elif illegChar.search(name):
        raise Exception('invalid name: %s' % name)
    return name

# auxiliary class used to supoort syntax 'as' in select
class _markAS:
    def __init__(self, name, copy=0):
        self.name=name
        self.copy=copy

    def __str__(self):
        return 'markAS(%s, %i)' % (self.name, self.copy)

    def __repr__(self):
        name=self.name.__repr__()
        return 'markAS(%s, %i)' % (name, self.copy)