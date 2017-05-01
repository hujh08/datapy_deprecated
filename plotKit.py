#!/usr/bin/env python3

'''
auxiliary functions used module plot
'''

import numpy as np
from numpy  import histogram
from scipy.optimize import curve_fit

from matplotlib.transforms import Transform

from functools import reduce

# when plot in multi-panel, determine nrow/ncol
def rectDecomp(num, maxr=2):
    '''
    for an integer d, find minimum n and correspoding m,
    in which:
        n*m>=d and 1<=n/m<maxr
    This method is just like find a rectangle which
        is most approximate to square and
        has area most approximate to a given number
    '''
    numSqrt=np.ceil(np.sqrt(num))
    factN=factM=numSqrt
    if numSqrt**2>num:
        # remainder=n*m-num
        re=numSqrt**2-num

        # max difference of two numbers
        maxd=np.floor(np.sqrt(num/maxr)*(maxr-1))
        maxd=int(maxd)
        #maxd=int(num)-1
        for d in range(1, maxd+1):
            m=np.ceil((-d+np.sqrt(d**2+4*num))/2)
            n=m+d
            reNow=n*m-num
            if reNow<re:
                re=reNow
                factN=n
                factM=m
                if re==0:
                    break

    if factN==numSqrt and num<numSqrt*np.floor(numSqrt/maxr):
        factM=np.ceil(num/factN)

    return int(factN), int(factM)

# auxiliary functions
def buildTicks(xmin, xmax,
               numTicks=5,
               precTicks=None):
    '''
    get ticks covering a given interval
    '''
    if precTicks==None:
        scope=xmax-xmin
        avSeq=scope/numTicks
        precTicks=10**np.ceil(np.log10(avSeq))
        precTicks2=10**np.ceil(np.log10(avSeq*2))/2
        if precTicks2<precTicks:
            precTicks=precTicks2

    # left-end tick
    lTick=np.floor(xmin/precTicks)*precTicks
    # right-end ticks
    rTick=np.ceil(xmax/precTicks)*precTicks

    return np.arange(lTick, rTick+precTicks, precTicks)

# 1d gaussian function
def gauss1d(x, I, x0, sigma):
    return I*np.exp(-(x-x0)**2/(2*sigma**2))

# function used in statistic
## hist of one of x, y, xe, ye
def histStat(x, y, xe, ye, key='x', normalize=None, **kwargs):
    data=locals()[key]
    hval, bin_edges=histogram(data, **kwargs)
    bin_cent=(bin_edges[:-1]+bin_edges[1:])/2
    bin_gap=bin_cent[1]-bin_cent[0]
    if normalize!=None:
        hval=hval/hval.sum(dtype='float64')
        hval*=normalize/bin_gap
    l=len(hval)
    return bin_cent, hval, [None]*l, [None]*l

def cumulStat(x, y, xe, ye, key='x', normalize=None, **kwargs):
    data=locals()[key]
    hval, bin_edges=histogram(data, **kwargs)
    bin_cent=(bin_edges[:-1]+bin_edges[1:])/2
    hcum=hval.cumsum()
    if normalize!=None:
        hcum=hcum/hcum[-1]
        hcum*=normalize
    l=len(hcum)
    return bin_cent, hcum, [None]*l, [None]*l

def gaussStat(x, y, xe, ye, init=None, **kwargs):
    if init==None:
        I0=np.max(y)
        mean0=np.average(x, weights=y)
        sigma0=reduce(lambda s, i, m=mean0: s+i[1]*(i[0]-m)**2,
                      zip(x, y), 0)
        sigma0=np.sqrt(sigma0/np.sum(y))
    else:
        I0, mean0, sigma0=init
    popt, pcov=\
        curve_fit(gauss1d, x, y, p0=[I0, mean0, sigma0])

    return popt, [None]*3, [None]*3, [None]*3

# factory of transform instance through a funciton
class TransformFactory(Transform):
    def __init__(self, func, indims, outdims=None,
                       inv_func=None):
        '''
        func: callable
            operates on array with `indims` elements,
            return array with `outdims` elements

        inv_func: callable
            inversive function of func

            inv_func(func(a))=a
        '''
        Transform.__init__(self)
        self.func=func
        self.inv_func=inv_func

        self.input_dims=indims

        if outdims==None:
            outdims=indims
        self.output_dims=outdims

    def inverted(self):
        if self.inv_func==None:
            raise NotImplementedError('inverted method '
                                      'not provided')
        return TransformFactory(self.inv_func,
                                self.output_dims,
                                self.input_dims,
                                self.func)

    def transform_non_affine(self, values):
        # in Transform.transform:
        #   values would be converted 2d array
        return np.apply_along_axis(self.func, 1, values)

class FuncTransform(TransformFactory):
    '''
    func handles elements of values independently
    '''
    is_separable=True

    def __init__(self, func, indims, outdims=None,
                       inv_func=None):
        '''
        func, inv_func: callable
        works on scalar
        '''
        func=np.frompyfunc(func, 1, 1)
        if inv_func!=None:
            inv_func=np.frompyfunc(inv_func)

        TransformFactory.__init__(self, func, indims,
                                        outdims, inv_func)

    def transform_non_affine(self, values):
        # in Transform.transform:
        #   values would be converted 2d array
        return self.func(values)


class Transform2DSwap(Transform):
    '''
    make new transform satisfies:
        yr, xr=new_transform(y, x)
        where
            xr, yr=old_transform(x, y)
    '''
    def __init__(self, trans):
        Transform.__init__(self)

        self.trans=trans
        self.set_children(trans)

        self.input_dims=trans.input_dims
        self.output_dims=trans.output_dims

        self.is_affine=trans.is_affine
        self.has_inverse=trans.has_inverse
        self.is_separable=trans.is_separable

    def transform_non_affine(self, values):
        values=np.c_[values[:, 1], values[:, 0]]
        res=self.trans.transform(values)
        return np.c_[res[:, 1], res[:, 0]]

# dynamically obtaining inverted instance of transform
class invTransform(Transform):
    '''
    simulate matplotlib.transforms.TransformWrapper
        but wrap the inverted of transform, not itself
    '''
    # access in monitor: to be delivered to self.trans_inv
    monitor_get={
        'transform',
        'transform_affine', 'transform_non_affine',
        'transform_path',
        'transform_path_affine', 'transform_path_non_affine',
        'get_affine', 'get_matrix',
        'is_separable', 'is_affine', 'has_inverse',
    }

    def __init__(self, trans):
        Transform.__init__(self)

        self.trans=trans
        self.set_children(trans)

        self.input_dims=trans.output_dims
        self.output_dims=trans.input_dims

        self._update_trans_inv()

    def _update_trans_inv(self):
        trans=self.trans.inverted()
        self.trans_inv=trans
        self._invalid=0

    def inverted(self):
        return self.trans

    def frozen(self):
        return invTransform(self.trans.frozen())

    def set(self, trans):
        """
        Replace the current original transform with another one.

        The new child must have the same number of
            input and output dimensions as the current.
        """
        if trans.input_dims!=self.input_dims or\
           trans.output_dims!=self.output_dims:
            msg = ('The new trans must have the same number of '
                   'input and output dimensions as the current.')
            raise ValueError(msg)

        self.trans=trans
        self.set_children(trans)

        self._update_trans_inv()

        self.invalidate()
        self._invalid=0

    def __eq__(self, other):
        return self.trans.__eq__(other)

    def __str__(self):
        return 'inverted of '+str(self.trans)

    def __repr__(self):
        return "invTransform(%r)" % self.trans

    def __getattribute__(self, prop):
        if prop in invTransform.monitor_get:
            if self._invalid:
                self._update_trans_inv()
            self=self.trans_inv
        return object.__getattribute__(self, prop)