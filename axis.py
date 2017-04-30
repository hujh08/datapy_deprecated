#!/usr/bin/env python3

'''
wrapping class of
    matplotlib.axes._subplots.AxesSubplot instance
'''

from functools import partial

class Axis:
    '''
    class wrapping axis which is used to
        intercept some plot tasks and
            store plotted objects if legend in the future
    '''

    # plot task that would be intercepted
    plot_tasks={
        'plot', 'scatter', 'errorbar', 'bar', 'step',
    }

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

    # some special treatment for original method
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

    def __getattr__(self, prop):
        if prop in Axis.plot_tasks:
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
