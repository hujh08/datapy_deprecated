#!/usr/bin/env python3

'''
class to manage plot task
'''

import numpy as np
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

        # backup
        self.backup()

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
            self._axesGeo=self.axes # represent its geometry
            self.axes=self.axes.flatten()
            self._axes=self.axes # real, no replicated axes
        else:
            self.fig=plt.figure()
            ax=self.fig.add_subplot(111)
            self.axes=[ax]*self.ndata
            self._axes=[ax] # real, no replicated axes
            # represent its geometry
            self._axesGeo=np.array([[ax]])

    def setFigFrom(self, figax):
        self.fig=figax.fig
        self.axes=figax.axes
        self._axes=figax._axes
        self._axesGeo=figax._axesGeo
        return self

    # backup data in order for filter
    def backup(self):
        self._xdatas, self._ydatas,\
        self._xerrs, self._yerrs=\
        self.xdatas, self.ydatas,\
        self.xerrs, self.yerrs
        return self

    def restore(self):
        self.xdatas, self.ydatas,\
        self.xerrs, self.yerrs=\
        self._xdatas, self._ydatas,\
        self._xerrs, self._yerrs
        return self

    # filter data to plot
    def filter(self, func):
        '''
        func: should have 4 arities,
              and args' order is x, y, xe, ye
                  e.g. lambda x, y, xe, ye: ... 
        '''
        xs, ys, xes, yes=[], [], [], []
        for i in range(self.ndata):
            xdata, ydata, xerr, yerr=\
                self._xdatas[i], self._ydatas[i],\
                self._xerrs[i],  self._yerrs[i]
            x, y, xe, ye=[], [], [], []
            for xye in zip(xdata, ydata, xerr, yerr):
                if func(*xye):
                    for l, ele in zip([x, y, xe, ye], xye):
                        l.append(ele)
            for l, ele in zip([xs, ys, xes, yes],
                              [x, y, xe, ye]):
                l.append(ele)
        self.xdatas, self.ydatas,\
        self.xerrs, self.yerrs=\
            xs, ys, xes, yes
        return self

    # plot functions
    ## scatter
    def plotScatter(self, color='blue', **kwargs):
        for i in range(self.ndata):
            otherKW={'color': color,
                     'linestyle': 'none',
                     'marker': 'o'}
            ax, xdata, ydata, xerr, yerr=\
                self.axes[i],\
                self.xdatas[i], self.ydatas[i],\
                self.xerrs[i],  self.yerrs[i]

            if xerr!=None:
                otherKW['xerr']=xerr
            if yerr!=None:
                otherKW['yerr']=yerr

            ax.errorbar(xdata, ydata, **otherKW, **kwargs)
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

    # set x/ylabel
    def set_xlabel(self, label):
        for ax in self._axesGeo[-1, :]:
            ax.set_xlabel(label)
        return self

    def set_ylabel(self, label):
        for ax in self._axesGeo[:, 0]:
            ax.set_ylabel(label)
        return self

    # add a baseline
    def addLine(self, *args, **kwargs):
        for ax in self._axes[0:self.ndata]:
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

    # mark panels or draw legend
    def mark(self, mark, loc=None, **kwargs):
        if len(self._axes)==1:
            if loc==None:
                loc='upper left'
            ax=self._axes[0]
            # bbox_transform is ax.transAxes by default
            ax.legend(ax.get_lines(), mark, loc=loc)
        else:
            if loc==None:
                loc=(0.1, 0.8)
            for ax, m in zip(self._axes, mark):
                #ax.legend(ax.get_lines(), [m],
                #          loc=loc, **kwargs)
                ax.annotate(m,
                            xy=loc,
                            xycoords='axes fraction',
                            #identical to
                            #xycoords=ax.transAxes,
                            **kwargs)
        return self

    # savefig or just show
    def save(self, figname=None):
        if figname==None:
            self.fig.show()
        else:
            self.fig.savefig(figname)

    # convenient method to access data
    def __getattr__(self, prop):
        if prop in ['xlim', 'ylim']:
            prop='get_%s' % prop
            return getattr(self._axes[0], prop)()

