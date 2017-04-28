#!/usr/bin/env python3

'''
devise a class to manage plot task
'''

import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties

from scipy.optimize import curve_fit

import numpy as np
from numpy  import histogram

from math import ceil
from functools import partial

from .plotKit import rectDecomp, gauss1d,\
                     histStat, cumulStat, gaussStat
from .toolKit import keyWrap, tabStr

class Plot:
    '''
    class to manage plot task
    '''
    def __init__(self, xdatas, ydatas=None,
                       xerrs=None, yerrs=None,
                       multip=True, nRowCol=None):
        '''
        x/ydatas, x/yerrs: nested iterable
            maximum nesting depth=2
            basic element must be
                number--int or float or
                string--usually used to histogram plot

            if nesting depth of given datas is 1,
                it will be converted to [datas] at first
            if the element in the top list is number/string
                it will be quoted in list
            only xdatas is required, others are optional
            
            finally all given data will be normalized to depth 3
                level 1: corresponding to collection of axes
                level 2: corresponding to collection of data
                            which would be plotted in each axis
                level 3: collection of data for a plot

        multip: bool, int, list, tuple, dict
            used in datas split

        nRowCol: iterable or Plot
            used in the layout of axes
        '''
        # obtain information of shape of data
        self.shape, xdatas=self.getDataShape(xdatas)
        self.ndata=len(xdatas)

        if ydatas!=None:
            shape, ydatas=self.getDataShape(ydatas)
            self.alignShape(shape)

        if xerrs!=None:
            shape, xerrs=self.getDataShape(xerrs)
            self.alignShape(shape)

        if yerrs!=None:
            shape, yerrs=self.getDataShape(yerrs)
            self.alignShape(shape)

        # normalize datas
        self.xdatas_base=self.normalizeData(xdatas)
        self.ydatas_base=self.normalizeData(ydatas)
        self.xerrs_base=self.normalizeData(xerrs)
        self.yerrs_base=self.normalizeData(yerrs)

        self.datas_dict={
            'x': self.xdatas_base,
            'y': self.ydatas_base,
            'xe': self.xerrs_base,
            'ye': self.yerrs_base,
        }
        self.datas_list=[
            self.xdatas_base,
            self.ydatas_base,
            self.xerrs_base,
            self.yerrs_base,
        ]

        # split datas according to the number of axis
        if multip is True:
            self.splitDatas()
        elif multip is False:
            self.splitDatas(naxes=1)
        elif type(multip)==int:
            self.splitDatas(naxes=multip)
        elif type(multip)==list:
            self.splitDatas(ndpa=multip)
        elif type(multip)==tuple:
            # multip=(ndpa,[naxs])
            self.splitDatas(*multip)
        elif type(multip)==dict:
            # only allow ndpa, naxs for the key
            self.splitDatas(**multip)
        else:
            raise Exception('unsupported type for multip: %s'
                                % typ(multip))

        # list of datas for plot
        self.plotd_dict={
            'x': self.xdatas,
            'y': self.ydatas,
            'xe': self.xerrs,
            'ye': self.yerrs,
        }
        self.plotd_list=[
            self.xdatas,
            self.ydatas,
            self.xerrs,
            self.yerrs,
        ]

        # lay out the axes
        if type(nRowCol)==Plot:
            self.copy_figax(nRowCol)
        else:
            self.set_figax(nRowCol=nRowCol)

        # not backup in init
        self.backuped=False

    # methods used to normalize datas
    def isBasicEle(self, data):
        '''
        return wheter data is number, string or
            other scalar, like numpy scalar type
        '''
        if hasattr(data, '__iter__') and\
           type(data)!=str:
            return False
        return True

    def alignShape(self, shape):
        '''
        align shape and self.shape
        two corresponding lengths should be same or one is 1
        '''
        if len(shape)!=self.ndata:
            if self.ndata==1:
                self.ndata=len(shape)
                self.shape*=self.ndata
            elif len(shape)==1:
                shape*=self.ndata
            else:
                raise Exception('datas must have same length')

        for i, l in enumerate(shape):
            if self.shape[i]!=l:
                if self.shape[i]==1:
                    self.shape[i]=l
                elif l!=1:
                    raise Exception('datas must have same shape')

    def normalizeData(self, datas):
        '''
        normalize datas to the shape self.shape
        '''
        if datas==None:
            datas=[[None]]

        if len(datas)!=self.ndata and len(datas)==1:
            datas=[i.copy() for i in datas*self.ndata]

        for i, d in enumerate(datas):
            if len(d)!=self.shape[i] and len(d)==1:
                datas[i]=d*self.shape[i]

        return datas

    def getDataShape(self, datas):
        '''
        obtain information of shape of datas
        call _getDataShape to do the work recursively

        datas: nested list with depth <= 2

        return:
            1, normalized data:
                datas with depth=1 will be expanded to [datas]
                every basic element should have nesting depth 2

            2, shape: list of length of child list
        '''
        if self.isBasicEle(datas):
            raise Exception('datas must be iterable')

        # nesting depth
        depth=self._getDataDepth(datas, 0)
        if depth>2:
            raise Exception('too deep nesting: %i' % depth)

        # shape
        if depth==1:
            return [len(datas)],[datas]

        shape=[]
        for i, data in enumerate(datas):
            if self.isBasicEle(data):
                datas[i]=[data]
                shape.append(1)
            else:
                shape.append(len(data))

        return shape,datas

    def _getDataDepth(self, datas, depth):
        '''
        recursively obtain shape depth of nested list
        shape is presented by structure:
            [len list_of_children's_shape]
        '''
        depth+=1
        depth0=depth
        for datasNow in datas:
            if not self.isBasicEle(datasNow):
                d=self._getDataDepth(datasNow, depth0)
                if d>depth:
                    depth=d
        return depth

    # split datas
    def splitDatas(self, ndpa=None, naxes=None):
        '''
        split datas according to the number of axes

        ndpa: number of datas per axes, int or iterable
            if number, split equally
            if iterable, its element gives
                the number of datas on each axes

        naxes: number of axes, int

        both formers are optional.
        But both None, ndpa=1, naxes=self.ndata
        And if ndpa is iterable, naxes is useless
        '''
        if ndpa!=None:
            if type(ndpa)==int:
                if naxes==None:
                    naxes=ceil(self.ndata/ndpa)
                ndpa=[ndpa]*naxes
            elif type(ndpa)!=list:
                raise Exception('unsupported type for ndpa: %s'
                                    % type(ndpa))
        elif naxes!=None:
            ndpa=[ceil(self.ndata/naxes)]*naxes
        else:
            ndpa=[1]*self.ndata

        # check ndpa
        for i in ndpa:
            if i<0:
                raise Exception('negative is not allowed '
                                'for ndpa')

        # set datas used in plot
        self.xdatas=self._splitDatas(self.xdatas_base, ndpa)
        self.ydatas=self._splitDatas(self.ydatas_base, ndpa)
        self.xerrs=self._splitDatas(self.xerrs_base, ndpa)
        self.yerrs=self._splitDatas(self.yerrs_base, ndpa)

    def _splitDatas(self, datas, ndpa):
        '''
        do really work for each datas
        ndpa: iterable
        '''

        result=[]
        i0=0
        for i in ndpa:
            if i0>=self.ndata:
                break
            result.append(datas[i0:(i0+i)])
            i0+=i
        return result

    ## method open to the user for do the split again
    def reSplit(self, *args, **kwargs):
        self.splitDatas(*args, **kwargs)

    # lay out the axes
    def set_figax(self, naxes=None, nRowCol=None):
        if nRowCol==None:
            if naxes==None:
                naxes=len(self.xdatas)
            nRowCol=rectDecomp(naxes)

        naxes=nRowCol[0]*nRowCol[1]
        if naxes==1:
            self.fig=plt.gcf()
            self.axes=[self.fig.gca()]
        else:
            fig, axes = \
                plt.subplots(nrows=nRowCol[0],
                             ncols=nRowCol[1],
                             sharex=True, sharey=True)
            fig.subplots_adjust(hspace=0.001, wspace=0.001)
            self.fig=fig
            self.axes=axes.flatten()

        # collect objects added to the figure
        #       which can be used for legend
        self.pltObjs=[[] for i in self.axes]

    def copy_figax(self, srcFig):
        if type(srcFig)!=Plot:
            raise Exception('cannot copy figax from %s'
                                % type(srcFig))

        self.fig=srcFig.fig
        self.axes=srcFig.axes
        self.pltObjs=srcFig.pltObjs


    # backup data in order for filter, data transform
    def backup(self):
        self.backuped=True

        self._xdatas_base=self._backup(self.xdatas_base)
        self._ydatas_base=self._backup(self.ydatas_base)
        self._xerrs_base=self._backup(self.xerrs_base)
        self._yerrs_base=self._backup(self.yerrs_base)

        return self

    def _backup(self, datas_base):
        return [i.copy() for i in datas_base]

    def restore(self):
        '''
        restore backuped data
        but the storage is not changed,
            which is same as the list storing datas to plot
        '''
        if not self.backuped:
            return self

        self._restore(self._xdatas_base, self.xdatas_base)
        self._restore(self._ydatas_base, self.ydatas_base)
        self._restore(self._xerrs_base, self.xerrs_base)
        self._restore(self._yerrs_base, self.yerrs_base)

        return self

    def _restore(self, src, dst):
        for d, s in zip(dst, src):
            d[:]=s

    # filter data for plot
    def filter(self, func):
        if not self.backuped:
            self.backup()

        for i in range(self.ndata):
            xdata=self._xdatas_base[i]
            ydata=self._ydatas_base[i]
            xerr=self._xerrs_base[i]
            yerr=self._yerrs_base[i]

            # collect valid data
            xBuff, yBuff, xeBuff, yeBuff=[], [], [], []
            for xye in zip(xdata, ydata, xerr, yerr):
                if func(*xye):
                    xBuff.append(xye[0])
                    yBuff.append(xye[1])
                    xeBuff.append(xye[2])
                    yeBuff.append(xye[3])

            # store data to datas_base
            self.xdatas_base[i][:]=xBuff
            self.ydatas_base[i][:]=yBuff
            self.xerrs_base[i][:]=xeBuff
            self.yerrs_base[i][:]=yeBuff

        return self

    # transform data in one axis
    def transformAlong(self, func, key='x'):
        '''
        key: only x, y, xe, ye acceptable
        '''
        if not self.backuped:
            self.backup()

        datas=self.datas_dict[key]

        for data in datas:
            for i, d in enumerate(data):
                data[i]=func(d)

        return self

    # transform data for x, xe, y, ye
    def transform(self, func):
        '''
        func: callable
            must accept 4 positional arguments
                which correspoind to x, y, xe, ye
        '''
        if not self.backuped:
            self.backup()

        for xd, yd, xe, ye in zip(*self.datas_list):
            for i, xye in enumerate(zip(xd, yd, xe, ye)):
                xd[i], yd[i], xe[i], ye[i]=func(*xye)

        return self

    # statistic of data in one axis
    def statisticAlong(self, func, key='x'):
        '''
        key: only x, y, xe, ye acceptable

        func: callable
            only accept a iterable to
                do some statistic work
                and return iterable
        '''
        if not self.backuped:
            self.backup()

        xye_map={'x':0, 'y': 1, 'xe':2, 'ye':3}
        xyeInd=xye_map[key]
        del xye_map[key]

        for xye in zip(*self.datas_list):
            data=xye[xyeInd]
            data[:]=func(data)

            # drop other datas
            for i in xye_map.values():
                xye[i][:]=[None]*len(data)

        # update shape
        for i, d in enumerate(self.xdatas_base):
            self.shape[i]=len(d)

        return self

    # statistic of data in all four datas
    def statistic(self, func):
        '''
        key: only x, y, xe, ye acceptable

        func: callable
            accept 4 iterables to
                do some statistic work
                and return 4 iterables
        '''
        if not self.backuped:
            self.backup()

        for xye in zip(*self.datas_list):
            xyetmp=func(*xye)
            for dst, src in zip(xye, xyetmp):
                dst[:]=src

        # update shape
        for i, d in enumerate(self.xdatas_base):
            self.shape[i]=len(d)

        return self

    # visualization of data

    ## generic plot method in each axis.
    ##      maybe dependent between sets of data
    def gen_plot_ax(self, datas, pltFunc, *args, **kwargs):
        '''
        generic plot method for each axis
        plot of task for sets of data may be inter-dependent

        datas: collection of datas to plot
            like [self.xdatas, self.ydatas]

        pltFunc: plot function
            accept ax and datas, do the plot work
                return collection of objects needed for legend
        '''
        for ax, objs, *ads in zip(self.axes, self.pltObjs, *datas):
            #if 'collection' in pltFunc.__code__.co_varnames:
            #    kwargs['collection']=objs
            objcol=pltFunc(ax, *ads, *args, **kwargs)
            if objcol!=None and objcol:
                objs.extend(objcol)

    ## generic plot method. independent between sets of data
    def gen_plot(self, datas, pltFunc, *args, **kwargs):
        '''
        generic plot method for each set of data
        plot of task for sets of data is independent

        datas: collection of datas to plot
            like [self.xdatas, self.ydatas]

        pltFunc: factory function
            accept ax, and return function to plot
        '''
        for ax, objs, *ads in zip(self.axes, self.pltObjs, *datas):
            pltFuncAx=pltFunc(ax)
            for d in zip(*ads):
                obj=pltFuncAx(*d, *args, **kwargs)
                if type(obj)==list:
                    objs.extend(obj)
                elif obj!=None:
                    objs.append(obj)

    ## simple plot. just show raw data
    def plot(self, *args, **kwargs):
        self.gen_plot(self.plotd_list[:2], 
                      lambda ax: ax.plot,
                      *args, **kwargs)
        return self

    def scatter(self, *args, **kwargs):
        self.gen_plot(self.plotd_list[:2], 
                      lambda ax: ax.scatter,
                      *args, **kwargs)
        return self

    def errorbar(self, *args, **kwargs):
        self.gen_plot(self.plotd_list, 
                      lambda ax: ax.errorbar,
                      *args, **kwargs)
        return self

    def step(self, *args, **kwargs):
        self.gen_plot(self.plotd_list[:2], 
                      lambda ax: ax.step,
                      *args, **kwargs)
        return self

    ## other understanding of data
    ### as arguments of function
    def plotFunc(self, func, key='x',
                             scope=None,
                             npoint=10000,
                             **kwargs):
        '''
        datas in store are arguments of a function
        plot this funcion curve with these arguments

        scope: iterable
            giving the scope of x

        npoint: int

        '''
        if scope==None:
            scope=self.xlim

        def funcArray(ax, datas, func=func,
                                 scope=scope,
                                 npoint=npoint, 
                                 **kwargs):
            xmax, xmin=scope
            dx=(xmax-xmin)*1./npoint
            xd=np.arange(xmin, xmax, dx)
            yd=func(xd, *datas)
            return ax.plot(xd, yd, **kwargs)

        self.gen_plot([self.plotd_dict[key]],
                      lambda ax: partial(funcArray, ax),
                      **kwargs)

    ### as information to print
    #### generic method to print data in figure
    def printData_gen(self, func, key='x', loc=(0.8, 0.8),
                            coords='axes fraction',
                            **kwargs):
        '''
        datas in store are converted to string through func
        and be printed in  the figure
        '''
        def printFunc(ax, datas, func=func, loc=loc,
                            coords=coords,
                            fontfamily=None,
                            **kwargs):
            if 'fontfamily'!=None:
                font=FontProperties()
                font.set_family('monospace')
                kwargs['fontproperties']=font
            ax.annotate(func(datas), xy=loc,
                        xycoords=coords, **kwargs)

        self.gen_plot_ax([self.plotd_dict[key]], printFunc,
                         **kwargs)

    ##### more frequently used method
    def printData(self, head, field=None,
                        datasName=None, datasfield=None,
                        bstr=None,
                        pd=None, fv=None, hsep=None,
                        key='x', loc=(0.8, 0.8),
                        coords='axes fraction',
                        **kwargs):
        '''
        print data with given head

        head: iterable

        field: iterable or None
            show the scope of data to print

        datasName: iterable
            description of each set of data
            only be used when
                there are more than one sets of data

        bstr: callable
            convert each data--number or string to string

        pd: bool or None
            whether to print dname

        fv: bool or None
            whether to print fname one by one vertically

        hsep: string or None
            seperator in horizontal row
        '''

        dataStr=partial(tabStr, fname=head, field=field,
                            dname=datasName, dfield=datasfield,
                            bstr=bstr,
                            pd=pd, fv=fv, hsep=hsep)

        self.printData_gen(dataStr, key=key, loc=loc,
                            coords=coords, **kwargs)
        return self

    # bar plot
    #   where patches shouldn't overlap,
    #       different with gen_plot
    def _bar_plot_ax(self, ax, datas,
                           xticks=None,
                           width=0.8,
                           **kwargs):
        '''
        plot bar of datas in one ax
        '''
        if len(datas)==0:
            return

        collection=[]

        numbar=len(datas[0])
        xintTicks=np.array(range(numbar))

        ndata=float(len(datas))
        width=width/ndata
        shift=-width*(ndata-1)/2.
        for i, data in enumerate(datas):
            obj=ax.bar(xintTicks+shift, data, width, **kwargs)
            shift+=width
            collection.append(obj)

        if xticks!=None:
            ax.set_xticks(xintTicks)
            ax.set_xticklabels(xticks)

        return collection

    def bar(self, key='x',
                  xticks=None,
                  width=0.8,
                  **kwargs):

        barfunc=partial(self._bar_plot_ax, 
                            xticks=xticks, width=width)

        self.gen_plot_ax([self.plotd_dict[key]], barfunc,
                         **kwargs)

        return self

    ## complicated plot. pre-treatment needed.
    def hist(self, key='x', bins=50,
                   hrange=None,    # range of histogram,
                   normalize=None, # normalize to like 1 if set
                   onlyfit=False,  # only plot fitted line
                   fit=None,
                   flDict={}, # kwargs for fit line
                   fitAnnot=False,
                   faDict=None, # kwargs for annotation of fit
                   **kwargs
                   ):
        '''
        faDict: kwargs for annotation of fit
            default if set None:
                {xy=(0.60, 0.80),
                 fontsize=8,
                 xycoords='axes fraction',
                 horizontalalignment='left',
                 verticalalignment='center'}
        '''
        # keywords used in histogram
        hkwargs={}
        if hrange:
            hkwargs['range']=hrange

        self.statistic(partial(histStat,
                            key=key, bins=bins,
                            normalize=normalize, **hkwargs))

        if not onlyfit:
            self.step(**kwargs)

        if fit=='g':
            self.statistic(partial(gaussStat))
            self.plotFunc(gauss1d, **flDict)

            if fitAnnot:
                _faDict={
                    'loc': (0.60, 0.80),
                    'fontsize': 8,
                    'fontfamily': 'monospace',
                    'coords': 'axes fraction',
                    'ha': 'left',
                    'va': 'center',
                    'datasName': 'gauss%i',
                }
                if faDict!=None:
                    for i in faDict:
                        _faDict[i]=faDict[i]
                self.printData(['center', 'sigma'],
                               field=[1, 2], bstr='%.3f',
                               **faDict)

        return self

    ## cumulative fraction
    def cumul(self, key='x', bins=200,
                    hrange=None,    # range of histogram,
                    normalize=None, # normalize to like 1 if set
                    **kwargs
                    ):
        '''
        cumulative fraction
        '''
        # keywords used in histogram
        hkwargs={}
        if hrange:
            hkwargs['range']=hrange

        self.statistic(partial(cumulStat,
                            key=key, bins=bins,
                            normalize=normalize,
                            **hkwargs))
        self.plot(**kwargs)
        return self

    # divided to subgroup and plot
    def subgplot(self, subgs, key='x',
                       normalize=1,
                       width=0.8,
                       **kwargs):
        '''
        subgs: iterable
        '''
        # function to count the number in subgroups
        def cntSubgs(data, subgs=subgs):
            count={i: 0 for i in subgs}
            for d in data:
                if d in count:
                    count[d]+=1
            count_sort=[count[i] for i in subgs]
            if normalize:
                numtot=sum(count_sort)
                count_sort=[i*normalize/numtot
                                for i in count_sort]
            return count_sort
        
        self.statisticAlong(cntSubgs, key)
        self.bar(key, subgs, width, **kwargs)

        return self


    # decoration of the figure
    ## set x/ylim
    def set_xlim(self, xlim):
        for ax in self.axes:
            ax.set_xlim(xlim)
        return self

    def set_ylim(self, ylim):
        for ax in self.axes:
            ax.set_ylim(ylim)
        return self

    ## set x/yscale
    def set_xscale(self, scale):
        for ax in self.axes:
            ax.set_xscale(scale)
        return self

    def set_yscale(self, scale):
        for ax in self.axes:
            ax.set_yscale(scale)
        return self

    ## set x/yticks
    def set_xticks(self, ticks):
        for ax in self.axes:
            ax.set_xticks(ticks)
        return self

    def set_ytics(self, ticks):
        for ax in self.axes:
            ax.set_yticks(ticks)
        return self

    ## set x/ylabel
    def set_xlabel(self, label):
        for ax in self.axes:
            if ax.is_last_row():
                ax.set_xlabel(label)
        return self

    def set_ylabel(self, label):
        for ax in self.axes:
            if ax.is_first_col():
                ax.set_ylabel(label)
        return self

    ## add a baseline
    def addLine(self, *args, **kwargs):
        for ax in self.axes[0:self.ndata]:
            ax.plot(*args, **kwargs)
        return self

    def addEqline(self, scope=None, color='black'):
        if scope==None:
            xlim=self.xlim
            ylim=self.ylim
            scope=[min(xlim[0], ylim[0]), 
                   max(xlim[1], ylim[1])]
        self.addLine(scope, scope,
                     color=color)
        return self

    def addHline(self, base=0, scope=None, color='black'):
        # add horizental line
        if scope==None:
            scope=self.xlim
        self.addLine(scope, [base, base], color=color)
        return self

    def addVline(self, base=0, scope=None, color='black'):
        # add vertical line
        if scope==None:
            scope=self.ylim
        self.addLine([base, base], scope, color=color)
        return self

    ## mark axes
    def mark(self, mark,
                   loc=(0.1, 0.8),
                   coords='axes fraction',
                   **kwargs):
        for ax, m in zip(self.axes, mark):
            ax.annotate(m, xy=loc, xycoords=coords, **kwargs)
        return self

    ## legend
    def legend(self, labels, objs=None,
                     loc='upper right',
                     **kwargs):
        '''
        objs: iterable or None
            iterable: containing integer,
                representing which objects in each axes
            None: all objects
        '''
        handlabs=[labels]
        if objs!=None:
            handlabs.insert(0, [
                [psAx[i] for i in iAx]
                    for iAx, psAx in zip(objs, self.pltObjs)
            ])
        for ax, *labs in zip(self.axes, *handlabs):
            ax.legend(*labs, loc=loc, **kwargs)
        return self

    # savefig or just show
    def save(self, figname=None):
        if figname==None:
            self.fig.show()
        else:
            self.fig.savefig(figname)
        plt.close()

    # convenient method to access data
    def __getattr__(self, prop):
        if prop in ['xlim', 'ylim']:
            prop='get_%s' % prop
            return getattr(self.axes[0], prop)()