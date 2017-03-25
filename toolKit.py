#!/usr/bin/env python3

'''
some auxiliary functions/classes
'''

# identical transform
idtrans=lambda x: x

#import re

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
        if sep==None:
            key=idtrans
        else:
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

# make lists has the same length
def listBroadCast(lcontainer):
    if len(lcontainer)<2:
        return lcontainer

    lLens=filter(lambda i: i!=1, map(len, lcontainer))
    lLens=list(lLens)
    if not lLens:
        return lcontainer

    l=lLens[0]
    for i in lLens[1:]:
        if i!=l:
            raise Exception('mismatch length for lists')

    for i, ele in enumerate(lcontainer):
        if len(ele)==1:
            lcontainer[i]*=l

    return lcontainer

# convert to regexp used to find specified word(s)
# mainly escaping all characters which are special in regexp
#        and appending \b
#specRe=re.compile(r'(\.)')
def toRePattern(s):
    if type(s)==list or type(s)==tuple:
        return [toRePattern(i) for i in s]

    #return specRe.sub(r'\\\1', s)
    return r'\b%s\b' % s.replace('.', r'\.')

# infinite iterator
class infIter:
    '''
    implement infinite iterator
    for example:
        simple:
            infinite None sequence:
                infIter()
            arithmetic sequence:
                infIter(0, lambda x: x+1)
        more complicated
            fibonacci sequence:
                infIter([1, 1],
                        lambda x: [x[1], x[0]+x[1]],
                        lambda x: x[0])
    in order to stop:
        use break or
        used in zip with a finite iterator
    '''
    def __init__(self, state=None,
                 iter=None, key=None):
        self.state=state
        self.state0=self.state  # initial state

        # iteration function
        if iter==None:
            iter=idtrans
        self.ifunc=iter

        # wrapper of returning val
        if key==None:
            key=idtrans
        self.kfunc=key

    def reset(self):
        '''
        reset state of iterator
        '''
        self.state=self.state0

    def __iter__(self):
        return self

    def __next__(self):
        state=self.state
        self.state=self.ifunc(state)
        return self.kfunc(state)

## some special infinite iterators
### infinite None
infNone=infIter()
### arithmetic sequence
def ariSeq(a=0, d=1):
    return infIter(a, lambda x: x+d)
### geometric sequence
def geoSeq(a=1, t=2):
    return infIter(a, lambda x: x*t)

# n-dimension list
class ndList:
    '''
    n-dimension list
    simpe wrapper of list,
    and has tuple index
    '''
    def __init__(self, *shape):
        # shape is tuple
        self.layout(*shape)
    
    # lay out sublist
    def _layout(self, shape):
        '''
        layout sublist
        '''
        if len(shape)==1:
            return [[] for i in range(*shape)]
        return [self._layout(shape[1:])
                    for i in range(shape[0])]

    def layout(self, *shape):
        self.shape=shape
        self.container=self._layout(shape)

    # fill data
    def fill(self, index, d):
        if type(index)==int:
            index=(index,)
        if len(index)!=len(self.shape):
            raise Exception('mismatch dimension '+
                            'of index with shape')

        self[index].append(d)
        return self

    # clear data in sublist
    def clear(self, index=None):
        if index==None:
            self.container.clear()
            return self

        self[index].clear()
        return self

    def __getitem__(self, index):
        if type(index)==int:
            return self.container[index]
        elif type(index)==tuple:
            result=self.container
            for i in index:
                result=result[i]
            return result
        else:
            raise TypeError('ndList indices must be '+
                            'integers or tuple')

    def __str__(self):
        return self.container.__str__()
    def __repr__(self):
        return self.container.__repr__()
