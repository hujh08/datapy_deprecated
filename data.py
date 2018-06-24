#!/usr/bin/env python3

# class for a data table

from .funcs import readtxt

class Data:
    def __init__(self, fname):
        
        # use list, not numpy.record, for its shape is mutable
        #     at the same time, provide a method to convert to record
        self.head, self.data, self.fmt=readtxt(fname)
        if self.head==None:
            self.head=['col%i' % i for i in range(self.width)]

    # shape of data
    @property
    def width(self):
        return len(self.fmt)

    @property
    def length(self):
        return len(self.data)

    # to numpy.record
    def array(self):
        import numpy as np
        dtype=self.fmt.dtype(self.head)
        data=list(map(tuple, self.data))
        return np.array(data, dtype=dtype)