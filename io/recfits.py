#!/usr/bin/env python3

'''
    io of record FITS file
'''

import sys
import numbers
from functools import partial

import numpy as np
import pandas as pd

def load_rec_fits(fname, **kwargs):
    d=load_fits_data(fname)

    return rec_to_df(d, **kwargs)

def rec_to_df(record, fields_ext=None, fields_exclude=set(),
                # parameters for field name
                field_rename={}, fieldname_charcase=None,
                # parameters for transpose of suba
                suba_transpose=False,
                # parameters for multilevel column
                names_multilevel_by_field={},
                constructor_multilevel_colname=None,
                ## parameters for default constructor
                formatter_levelno=None, labels_of_leveldim=[],
                level_suba_squeeze=False,
                ## squeeze multi-level
                colname_squeeze=False,
                # other parameters
                force_native=True,
                use_multiindex_col=True):
    '''
        record data to DataFrame

        Parameters:
            fields_ext: None, list or dict
                fields of record to extract

                if dict, order in result is same as record

            fields_exclude: dict or set
                fields to exclude in result

            ==== determine fields of result ====
                use `fields_ext` and `fields_exclude` in order
            ====================================

            field_rename: dict
                {old_name: new_name}
                rename field

                NOTE: if set, name in later processes would be new one

            fieldname_charcase: None, 'upper' or 'lower'
                char case of field name

                NOTE: it not works for field in `field_rename`

            ======================================
            suba_transpose: bool, dict, or Iterable, default `False`
                transpose for sub-array field

                if False, no transpose

                if True, reverse dimension of suba
                    e.g. shape of data in current field, (n, n0, n1, n2)
                        where n is number of sample
                            (n0, n1, n2) is shape of sub-array
                        after transpose, it becomes (n, n2, n1, n0)

                if dict, with format {field_name: value}
                    where value could be bool,
                        or axes, passed to np.transpose

                if other iterable type, it specify set of fields to transpose

            ======================================
            names_multilevel_by_field: dict
                names of sublevels
                for a field, corresponding value is list of level name tuple

            constructor_multilevel_colname: None, or callable
                constuctor of name of multi-level column
                    used to support flexible column name constructing

                if None, use default constructor:
                    function `tuples_multilevel_colname`

                if callable,
                    input (name, shape) of the field and some optional keywords
                    return tuples of column names, as order of ravel of subarray
                        or None, if so, back to default constructor
                        which are then squeezed or not, by `colname_squeeze`

                    by flexibility, it can return everything as column name
                        if `colname_squeeze` is False

            # kw_default_mlc: dict
            #     optional keyword arguments for default constructor

            formatter_levelno, labels_of_leveldim, level_suba_squeeze:
                optional parameters for default constructor

            ==== construct of multilevel name ================================
                order in construction:
                    1, `names_multilevel_by_field`
                        used for simple level name

                    2, `constructor_multilevel_colname`:
                        flexible constructor, used for complicated situations

                    3, default constructor + optional parameters
                        default method
                        if previous methods are not given,
                            or None is returned by user-specified constructor
                        default one would then work

                        some of its features could also be customized by user

                rule for colname constrcting is
                    to implement simple name by
                        `names_multilevel_by_field` and default constructor
                    and complicated one in user-specified constructor
            ==================================================================

            colname_squeeze: bool, default `False`
                use for multi-level column name,
                    which is from subarray in record

                if True, combine levels with separator '_'

            ===== construct of colname =======================
                1, construct of multilevel name
                2, then squeeze by `colname_squeeze`
            ==================================================

            force_native: bool, default `True`
                wheter to convert data to native byteorder

            use_multiindex_col: bool, default `True`
                use MultiIndex for column
                    if there is any multilevel column
    '''
    dt=record.dtype

    # fields to extract: use `fields_ext` and `fields_exclude` in order
    fields=dt.names
    if fields_ext is not None:
        if isinstance(fields, dict):
            fields=[t for t in fields if t in fields_ext]
        else:
            fields=fields_ext

    if fields_exclude:
        fields=[t for t in fields if t not in fields_exclude]

    # sub-array transpose
    if not (isinstance(suba_transpose, dict) or isinstance(suba_transpose, bool)):
        assert not is_scalar_type(suba_transpose)

        # other iterable: convert to dict
        suba_transpose={t: True for t in suba_transpose}

    # constructor of multilevel column name
    kw=dict(formatter_levelno=formatter_levelno,
            labels_of_leveldim=labels_of_leveldim,
            level_suba_squeeze=level_suba_squeeze)
    constuctor_mlc_default=partial(tuples_multilevel_colname, **kw)

    if constructor_multilevel_colname is None:
        constructor_multilevel_colname=constuctor_mlc_default

    # extract data and name for columns
    data_cols=[]
    name_cols=[]
    max_col_level=1   # max height of column levels

    for name in fields:
        dcol=record[name]   # data of this col

        # byteorder
        if force_native:  # native order
            dcol=to_native_byteorder(dcol)

        tcol=dt[name]       # type of this col
        suba=tcol.shape     # shape of subarray, otherwise ()

        dcol=dcol.reshape(-1, *suba)

        # field rename: subsequent process would use new name
        if name in field_rename:
            name=field_rename[name]
        elif fieldname_charcase is not None:
            assert fieldname_charcase in ['upper', 'lower']
            name=getattr(name, fieldname_charcase)()

        # data which is not subarray-type
        if not suba:
            data_cols.append(dcol)
            name_cols.append(name)

            continue

        # subarray transpose
        if len(suba)>1:
            if isinstance(suba_transpose, dict):
                tp=suba_transpose.get(name, False)
            else:
                tp=suba_transpose

            ## determine axes to transpose
            axes_suba=np.arange(len(suba))+1
            if type(tp) is not bool:
                assert len(tp)==len(suba)
                
                axes=[axes_suba[i] for i in tp]
                assert np.unique(tp)

                tp=True
            elif tp:
                axes=np.flip(axes_suba)

            ## transpose
            if tp:
                dcol=np.transpose(dcol, (0, *axes))
                suba=dcol.shape[1:]

        # handle subarray type
        dcol=dcol.reshape(dcol.shape[0], -1)

        ## level names
        if name in names_multilevel_by_field:
            names_suba=names_multilevel_by_field[name]
            names=combine_name_field_suba(name, names_suba)
        else:
            names=constructor_multilevel_colname(name, suba)
            if names is None:
                names=constuctor_mlc_default(name, suba)

        ## colname squeeze
        if colname_squeeze:
            names=['_'.join(map(str, t)) for t in names]
        else:
            subls=[len(t) for t in names if not is_scalar_type(t)]
            max_col_level=max([max_col_level, *subls])

            # some validity check
            if subls:
                if min(subls)<=0:  # empty tuple exists
                    print('warning: empty tuple exists for field `%s`' % name)
            
                if np.any([t==1 for t in subls]):  # fetch out one-element tuple
                    print('warning: one-element tuple exists. to pick out it')
                    names=[(t if (is_scalar_type(t) or len(t)!=1) else t[0]) for t in names]

        data_cols.extend(dcol.T)
        name_cols.extend(names)

    # assemble DataFrame from `data_cols` and `name_cols`
    if use_multiindex_col and max_col_level>1:
        inds=[]
        for t in name_cols:
            if is_scalar_type(t):
                inds.append((t,)+tuple(['']*(max_col_level-1)))
            else:
                k=len(t)
                inds.append(tuple(t)+tuple(['']*(max_col_level-k)))
        name_cols=pd.MultiIndex.from_tuples(inds)

    dict_data=dict(zip(name_cols, data_cols))

    return pd.DataFrame(dict_data, columns=name_cols)

## auxilliary functions
def load_fits_data(fname):
    from astropy.io import fits
    return fits.getdata(fname)

### multilevel colnames
def tuples_multilevel_colname(name, shape, **kwargs):
    '''
        get tuples of name of multilevel column

        optional `kwargs`: all for `levelnames_by_shape`
            see it for details
    '''
    names_suba=levelnames_by_shape(shape, **kwargs)

    return combine_name_field_suba(name, names_suba)

def levelnames_by_shape(shape, formatter_levelno=None,
        labels_of_leveldim=[], level_suba_squeeze=False):
    '''
        level names for a given shape of sub-array

        Parameters:
            formatter_levelno: None or str
                use [0, 1, 2,...] as labels by default

                if str, must be format string, like 'c%i',
                    which only accpets one integer as input

            labels_of_leveldim: iterable
                contain vectors with different length
                    one vector correspond to a level with same dim

                elements in the set must not be scalar type
                    and must have different length

            level_suba_squeeze: bool, default `False`
                whether or not squeeze sub-array levels
    '''
    # not empty and all positive integer
    assert len(shape)>=1
    assert np.all([isinstance(t, int) and t>0 for t in shape])

    # for one-level
    kw=dict(formatter_levelno=formatter_levelno)
    func_onelevel=partial(names_of_onelevel, **kw)

    # dict of level names indexed by level dim
    dict_leveldim={}
    for t in labels_of_leveldim:
        assert not is_scalar_type(t)
        assert len(t) not in dict_leveldim  # no duplicated length

        dict_leveldim[len(t)]=t

    # construct names level by level
    levels=[]
    for n in shape:
        if n in dict_leveldim:
            names=dict_leveldim[n]
        else:
            names=func_onelevel(n)

        levels.append(names)

    inds=pd.MultiIndex.from_product(levels)

    if level_suba_squeeze:
        inds=['_'.join(map(str, t)) for t in inds]

    return inds

def names_of_onelevel(n, formatter_levelno=None):
    '''
        names of one level
            which is of length `n`
    '''
    inds=np.arange(n)
    if formatter_levelno is not None:
        inds=[formatter_levelno % i for i in inds]

    return inds

def combine_name_field_suba(name, names_suba):
    '''
        combine field name and sub-array names

        Parameters:
            name: name of field

            names_suba: names of subarray
    '''
    names_suba=[((t,) if is_scalar_type(t) else tuple(t)) for t in names_suba]

    return [(name,)+t for t  in names_suba]

### for dtype
def to_native_byteorder(data):
    '''
        convert to native byteorder of the platform
    '''
    dt=data.dtype

    if dt.isnative:
        return data

    # native_code=(sys.byteorder=='little') and '<' or '>'
    return data.astype(dt.newbyteorder(sys.byteorder))

def is_scalar_type(d):
    '''
        wheter type of data is scalar
    '''
    return isinstance(d, str) or isinstance(d, numbers.Number)
