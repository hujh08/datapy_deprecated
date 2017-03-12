#!/usr/bin/env python3

'''
class to manage plot task
'''

import matplotlib.pyplot as plt

from .plotKit import rectDecomp

class Plot:
    '''
    manage plot task
    '''
    def __init__(self, xdatas, ydatas,
                       xerrs=None, yerrs=None,
                       multip=True, nRowCol=None):
        '''
        mulitp: bool
            plot in multi-panel or together
        '''
        if xdatas==None:
            xdatas=[None]
        if ydatas==None:
            ydatas=[None]
        # broadcast axis with length=1 to match another axis
        xlen=len(xdatas)
        ylen=len(ydatas)
        if xlen==1:
            xdatas*=ylen
        elif ylen==1:
            ydatas*=xlen
        elif xlen!=ylen:
            raise Exception('mismatch length of x/ydata')

        # handle some special format
        for i, (x, y) in enumerate(zip(xdatas, ydatas)):
            if x==None:
                xdatas[i]=range(len(y))
            elif y==None:
                ydatas[i]=range(len(x))
            # when x is int/float and y is list
            elif not hasattr(x, '__iter__') and \
                     hasattr(y, '__iter__'):
                xdatas[i]=[x]*len(y)
            elif not hasattr(y, '__iter__') and \
                     hasattr(x, '__iter__'):
                ydatas[i]=[y]*len(x)
            # when x/y are both int/float, plt can handle this

        self.xdatas=xdatas
        self.ydatas=ydatas
        self.ndata=len(xdatas)  # number of data

        # handle error
        xyerrs=[]
        for errs in [xerrs, yerrs]:
            if errs==None:
                xyerrs.append([None]*self.ndata)
                continue
            if len(errs)==1:
                xyerrs.append(errs*self.ndata)
            elif len(errs)!=self.ndata:
                raise Exception('wrong length for x/yerr')
        self.xerrs, self.yerrs=xyerrs

        # set matplotlib
        self.initFig(multip=multip, nRowCol=nRowCol)

    # initate setup of matplotlib
    def initFig(self, multip=True, nRowCol=None):
        # matplotlib object
        if multip or nRowCol!=None:
            if nRowCol==None:
                nRowCol=rectDecomp(self.ndata)
            self.fig, self.axes = \
                plt.subplots(nrows=nRowCol[0],
                             ncols=nRowCol[1],
                             sharex=True, sharey=True)
            self.fig.subplots_adjust(hspace=0.001, wspace=0.001)
            self.axes=self.axes.flatten()

        else:
            self.fig=plt.figure()
            ax=self.fig.add_subplot(111)
            self.axes=[ax]*self.ndata

    def plotScatter(self, color='blue'):
        for ax, xdata, ydata in zip(self.axes,
                                    self.xdatas,
                                    self.ydatas):
            ax.scatter(xdata, ydata, color=color)

    def save(self, figname=None):
        if figname==None:
            self.fig.show()
        else:
            self.fig.savefig(figname)
