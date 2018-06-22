#!/usr/bin/env python3

'''
functions to read text file
'''


def readtxt(fname):
    from .fmt import Format
    data=[]
    fmt=Format()
    with open(fname) as f:
        # treat first line, no matter whether started with '#'
        hdline=f.readline()

        # if first line starts with '#'
        #     skip next some lines started with '#'
        if hdline.startswith('#'):
            for line in f:
                if not line.startswith('#'):
                    _parseline(line, data, fmt)

        for line in f:
            _parseline(line, data, fmt)

    # cope with head line
    if hdline.startswith('#'):
        head=hdline[1:].split()
        if len(head)!=len(fmt):
            # treat it as comment
            head=None
    else:
        # if all fields is string, but not for data, treat it as head
        fields=hdline.split()
        if len(fields)!=len(fmt):
            raise Exception('mismatch fields in first line')

        hdfmt=Format(fields)
        if hdfmt.all_isstr() and not fmt.all_isstr():
            head=fields
        else:
            head=None
            data.insert(0, fields)
            fmt.update(hdfmt)

    if not fmt.all_isstr():
        list(map(fmt, data))
        # from multiprocessing.dummy import Pool as ThreadPool
        # pool=ThreadPool(4)
        # pool.map(fmt, data)
        # pool.close()
        # pool.join()

    return head, data, fmt

def _parseline(line, data, fmt):
    '''
    parse a line, mainly
        1, split to fields
        2, data type for each fields
        2, number of fields

    Parameters:
        data, fmt: containers, change in-place
            data: store fields of the line
            fmt: store format of lines until now
                see `fmt` for detail

    fmt:
        it is `dict`, including keys:
    '''
    fields=line.split()
    data.append(fields) # collect data
    fmt.update(fields)  # update fields
