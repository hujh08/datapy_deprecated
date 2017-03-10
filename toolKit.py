#!/usr/bin/env python3

'''
some auxiliary functions/classes
'''

def keyWrap(key=None):
    '''
    convert key to a function
    key could be None/str/function
        None: identity function
        str: e.g. '%ssuffix'
        funcion: e.g. lambda x: '%ssuffix' % x
    '''

    if key==None:
        key=lambda x: x
    elif type(key)==str:
        # if omitting key=key, key in lambda is global
        key=lambda x, key=key: key % x
    elif not callable(key):
        raise Exception('unsupported type for keyFunc')

    return key

# delete char in index
def strDelIn(s, index):
    return s[0:index]+s[(index+1):]