#!/usr/bin/env python3

'''
    io of text file
'''
import pandas as pd

# text file
def load_txt(fname, head, cols, dtypes={}, cols_rename={}, delim_whitespace=True):
    '''
        load text file

        Parameters
            fname: string
                data file name

            head:
                head for log file

            cols:
                cols to return
    '''
    return pd.read_csv(fname, delim_whitespace=delim_whitespace)
