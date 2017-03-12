#!/usr/bin/env python3

'''
auxiliary functions used module plot
'''

import numpy as np
from scipy.optimize import curve_fit

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