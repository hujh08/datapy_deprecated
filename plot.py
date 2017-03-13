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
            elif not hasattr(y, '__iter__') and \
                 not hasattr(x, '__iter__'):
                 xdatas[i]=[x]
                 ydatas[i]=[y]

        self.xdatas=xdatas
        self.ydatas=ydatas
        self.ndata=len(xdatas)  # number of data

        # handle error
        xyerrs=[]
        for errs in [xerrs, yerrs]:
            if errs==None:
                xyerrs.append([None]*self.ndata)
                continue
            if not hasattr(errs, '__iter__'):
                errs=[errs]*self.ndata
            elif len(errs)==1:
                errs*=self.ndata
            elif len(errs)!=self.ndata:
                raise Exception('wrong length for x/yerr')

            for i in range(self.ndata):
                if errs[i]==None:
                    continue
                if not hasattr(errs[i], '__iter__'):
                    errs[i]=[errs[i]]
                if len(errs[i])==1:
                    errs[i]*=len(self.xdatas[i])
            xyerrs.append(errs)

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
            self._axes=self.axes # real, no replicated axes
        else:
            self.fig=plt.figure()
            ax=self.fig.add_subplot(111)
            self.axes=[ax]*self.ndata
            self._axes=[ax] # real, no replicated axes

    # convenient method to access data
    def __getattr__(self, prop):
        if prop in ['xlim', 'ylim']:
            prop='get_%s' % prop
            return getattr(self._axes[0], prop)()

    # plot functions
    ## scatter
    def plotScatter(self, color='blue'):
        for i in range(self.ndata):
            kwargs={'color': color,
                    'linestyle': 'none',
                    'marker': 'o'}
            ax, xdata, ydata, xerrs, yerrs=\
                self.axes[i],\
                self.xdatas[i], self.ydatas[i],\
                self.xerrs[i],  self.yerrs[i]

            if xerrs!=None:
                kwargs['xerr']=xerrs
            if yerrs!=None:
                kwargs['yerr']=yerrs

            ax.errorbar(xdata, ydata, **kwargs)
        return self

    # set x/ylim
    def set_xlim(self, xlim):
        for ax in self._axes:
            ax.set_xlim(xlim)
        return self

    def set_ylim(self, ylim):
        for ax in self._axes:
            ax.set_ylim(ylim)
        return self

    # add a baseline
    def addLine(self, *args, **kwargs):
        for ax in self._axes:
            ax.plot(*args, **kwargs)
        return self

    def addEqline(self, color='black'):
        xlim=self.xlim
        ylim=self.ylim
        minxy=min(xlim[0], ylim[0])
        maxxy=max(xlim[1], ylim[1])
        self.addLine([minxy, maxxy], [minxy, maxxy],
                     color=color)
        return self

    def addHline(self, base=0, color='black'):
        # add horizental line
        self.addLine(self.xlim, [base, base], color=color)
        return self

    def addVline(self, base=0, color='black'):
        # add vertical line
        self.addLine([base, base], self.ylim, color=color)
        return self

    def save(self, figname=None):
        if figname==None:
            self.fig.show()
        else:
            self.fig.savefig(figname)
