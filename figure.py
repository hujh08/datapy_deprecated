#!/usr/bin/env python3

'''
container of axes
'''

import matplotlib.pyplot as plt

from .plotKit import rectDecomp
from .axis import Axis

class Figure:
    '''
    just used as container of axes
    '''
    def __init__(self, nRowCol=None, naxes=1):
        if nRowCol==None:
            nRowCol=rectDecomp(naxes)

        naxes=nRowCol[0]*nRowCol[1]
        if naxes==1:
            self.fig=plt.gcf()
            self.axes=[Axis(self.fig.gca())]
        else:
            fig, axes = \
                plt.subplots(nrows=nRowCol[0],
                             ncols=nRowCol[1],
                             sharex=True, sharey=True)
            fig.subplots_adjust(hspace=0.001, wspace=0.001)
            self.fig=fig
            self.axes=[Axis(a) for a in axes.flatten()]

        self.naxes=len(self.axes)

    def __iter__(self):
        self.ind=0
        return self

    def __next__(self):
        if self.ind>=self.naxes:
            raise StopIteration('iterator of Figure stops')
        ax=self.axes[self.ind]
        self.ind+=1
        return ax

    def __getitem__(self, prop):
        return self.axes[prop]

    def __getattr__(self, prop):
        return getattr(self.fig, prop)