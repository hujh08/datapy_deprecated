#!/usr/bin/env python3

'''
manager several data text file
and also do some visualization work
'''

from .data import Data
from .toolKit import keyWrap

class DataBase:
    def __init__(self, fnames=None,
                       tables=None,
                       pcols=0,   # primary key like SQL
                       key=None,
                       fkey=None):
        '''
        key: convert each name in format
             real name to store tables is format(name)

             str or function:
             str: e.g. '%ssuffix'
             funcion: e.g. lambda x: '%ssuffix' % x
        fkey: same as key, but act on fname
        '''
        # maintain 2 structures
        self.tables=[]   # real space to store data
        self.mapNames={}  # map from name to order

        key=keyWrap(key)
        fkey=keyWrap(fkey)

        if key==None:
            key=lambda x: x
        elif type(key)==str:
            # if omitting key=key, key in lambda is global
            key=lambda x, key=key: key % x

        if fnames!=None:
            if tables==None:
                tables=fnames

            if not hasattr(pcols, '__iter__'):
                pcols=[pcols]*len(fnames)

            for fname, table, p in zip(fnames, tables, pcols):
                self.addTable(key(table),
                              fkey(fname),
                              p)

    # convenient method accessing table
    def __getattr__(self, prop):
        if prop=='tNames':
            # names of table
            return [t.name for t in self.tables]

    def __getitem__(self, key):
        return self.tables[self.getTabInd(key)]

    # add table. If existed, overwrite
    def addTable(self, table, fname, pcol):
        d=Data(fname, name=table, pkey=pcol)
        if table not in self.mapNames:
            self.mapNames[table]=len(self.tables)
            self.tables.append(d)
        else:
            tableNo=self.mapNames[table]
            self.tables[tableNo]=d

    # get order of table
    def getTabInd(self, index):
        if type(index)==str:
            return self.mapNames[index]
        return index

    # merge all tables
    def mergeAll(self):
        result=self.tables[0].copy()

        result.wrapColName('%s.%%s' % self.tables[0].name)

        for table in self.tables[1:]:
            result.extend(table, wrap2='%s.%%s' % table.name)

        return result

