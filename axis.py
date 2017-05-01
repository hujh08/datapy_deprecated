#!/usr/bin/env python3

'''
wrapping class of
    matplotlib.axes._subplots.AxesSubplot instance
'''
import numpy as np
from matplotlib.font_manager import FontProperties
from matplotlib.transforms import blended_transform_factory

from functools import partial

from .toolKit import tabStr
from .plotKit import Transform2DSwap,\
                     FuncTransform, invTransform, gauss1d

# plot task that would be intercepted
plot_tasks={
    'plot', 'scatter', 'errorbar', 'bar', 'step',
}

class Axis:
    '''
    class wrapping axis which is used to
        intercept some plot tasks and
            store plotted objects if legend in the future
    '''
    def __init__(self, ax):
        self.ax=ax

        # storage of objects 
        self.objs=[]

    def plot_proxy(self, task, *args, store=True, **kwargs):
        '''
        proxy method of plot task of axis
        '''
        obj=getattr(self.ax, task)(*args, **kwargs)

        if store:
            if type(obj)==list:
                self.objs.extend(obj)
            elif obj!=None:
                self.objs.append(obj)
        return obj

    # special treatment to original method of self.ax
    def legend(self, labels, objs=None, **kwargs):
        '''
        objs: None or iterable
            if None, make legends of all objects in self.objs
            otherwise, objs is collection of integer
                which is index of object to legend
        '''
        if objs==None:
            objs_legend=self.objs
        else:
            objs_legend=self[objs]
        self.ax.legend(objs_legend, labels, **kwargs)

    def bars(self, datas, xticks=None, width=0.8, **kwargs):
        '''
        plot several bars without overlap

        datas: 2d iterable
            elements in datas have same length

        widthe: number
            total width of all bars
        '''
        if len(datas)==0:
            return

        numbar=len(datas[0])
        xintTicks=np.array(range(numbar))

        ndata=float(len(datas))
        width=width/ndata
        shift=-width*(ndata-1)/2.
        for i, data in enumerate(datas):
            self.bar(xintTicks+shift, data, width, **kwargs)
            shift+=width

        self.ax.set_xticks(xintTicks)
        if xticks!=None:
            self.ax.set_xticklabels(xticks)

    # function curve
    def fcurve(self, args, func, scope=(0, 1), npoint=100,
                     xtransform=None, **kwargs):
        '''
        transform: Transform instance
            determine transform of scope
        '''
        xmax, xmin=scope
        dx=(xmax-xmin)*1./npoint
        xd=np.arange(xmin, xmax+dx, dx)
        if xtransform==None:
            xtransform=self.ax.transAxes

        func=lambda x, f=func, args=tuple(args): f(x, *args)

        transData=self.ax.transData
        x2DataTrans=xtransform+invTransform(transData)
        y2DataTrans=Transform2DSwap(x2DataTrans)+\
                    FuncTransform(func, 2)
        ytransform=y2DataTrans+transData

        transform=blended_transform_factory(xtransform,
                                            ytransform)
        dataTrans=blended_transform_factory(x2DataTrans,
                                            y2DataTrans)

        return self.plot(xd, xd, transform=transform, **kwargs)

    # print datas in axis
    def dtext(self, datas, func=str, loc=(0.8, 0.8),
                    coords='axes fraction',
                    fontfamily=None, **kwargs):
        if 'fontfamily'!=None:
            font=FontProperties()
            font.set_family('monospace')
            kwargs['fontproperties']=font
        self.ax.annotate(func(datas), xy=loc,
                         xycoords=coords, **kwargs)

    ## datas is a 2d table
    def ttext(self, datas, fname, field=None,
                    dname=None, dfield=None, bstr=str,
                    pd=None, fv=None, hsep=None, **kwargs):
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

        kwargs: see dtext
        '''
        func=partial(tabStr, fname=fname, field=field,
                        dname=dname, dfield=dfield,
                        bstr=bstr, pd=pd, fv=fv, hsep=hsep)
        self.dtext(datas, func, **kwargs)

    def __getattr__(self, prop):
        if prop[0:3]=='ax_' and prop[3:] in plot_tasks:
            return partial(self.plot_proxy, prop)
        elif prop in plot_tasks:
            return partial(self.plot_proxy, prop)
        else:
            return getattr(self.ax, prop)

    def __getitem__(self, prop):
        if type(prop)==int:
            return self.objs[prop]
        elif type(prop)==slice:
            return self.objs[prop]
        elif prop==None:
            return self.objs[:]
        else:
            return [self[i] for i in prop]
