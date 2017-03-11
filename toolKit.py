#!/usr/bin/env python3

'''
some auxiliary functions/classes
'''

# return function used to wrap an input string
#     which has no keyword arguments
def keyWrap(key=None, sep=''):
    '''
    convert key to a function
    key could be None/str/function
        None: identity function
        str: e.g. '%ssuffix', '{0}'
        funcion: e.g. lambda x: '%ssuffix' % x
    seq:
        when key is None, used to join arguments
    '''
    if key==None:
        key=lambda *x: sep.join(x)
    elif type(key)==str:
        # if omitting key=key, key in lambda is global
        if key.find('%')!=-1:
            key=lambda *x, key=key: key % x
        else:
            key=key.format
    elif not callable(key):
        raise Exception('unsupported type for keyFunc')
    return key

# delete char in index
def strDelIn(s, index):
    return s[0:index]+s[(index+1):]

def strInsert(s, c, index):
    return s[0:index]+c+s[index:]

# flatten list
def listFlat(l, skipTuple=False):
    result=[]
    for ele in l:
        if not hasattr(ele, '__iter__') or \
           type(ele)==str or \
           (type(ele)==tuple and skipTuple):
            result.append(ele)
        else:
            result.extend(listFlat(ele))
    return result