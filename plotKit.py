#!/usr/bin/env python3

'''
auxiliary functions used module plot
'''

import numpy as np
from numpy  import histogram
from scipy.optimize import curve_fit

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