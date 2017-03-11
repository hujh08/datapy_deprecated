#!/usr/bin/env python3

'''
manager several data text file
and make visualization

future work:
    1, '.' is special character
       when column/table name contains '.',
           the way that is adopted now is to
           try different combination
       e.g. t1.t2.col1
           2 possibilities: t1+t2.col1, t1.t2+col1
           if both exist, raise exception
       '.' in column name and table name should be
            removed/converted to another character, like '_'
'''

from functools import partial

from .data import Data
from .toolKit import keyWrap, listFlat

class DataBase:
    def __init__(self, fnames=None,
                       tables=None,
                       pcols=0,   # primary key like SQL
                       wrap=None,
                       fwrap=None):
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
        # one auxiliary structure
        self._alias={}

        if fnames!=None:
            wrap=keyWrap(wrap)
            fwrap=keyWrap(fwrap)

            if tables==None:
                tables=fnames

            if not hasattr(pcols, '__iter__'):
                pcols=[pcols]*len(fnames)

            for fname, table, p in zip(fnames, tables, pcols):
                self.addFile(wrap(table),
                             fwrap(fname),
                             p)

    # convenient method accessing table
    def __getattr__(self, prop):
        if prop=='tNames':
            # names of table
            return [t.name for t in self.tables]

    def __getitem__(self, key):
        return self.tables[self.getTabInd(key)]

    def __contains__(self, member):
        if member in self.mapNames or \
           member in self._alias:
            return True
        return False

    # add table. If existed, overwrite
    def addFile(self, name, fname, pcol):
        d=Data(fname, name=name, pkey=pcol)
        return self.addTable(d)

    def addTable(self, table):
        name=table.name
        if name not in self.mapNames:
            self.mapNames[name]=len(self.tables)
            self.tables.append(table)
        else:
            tableNo=self.mapNames[name]
            self.tables[tableNo]=table
        return self

    # alias name of table
    def alias(self, name, alias):
        self._alias[alias]=name
        return self

    def aliasClear(self):
        self._alias.clear()

    # get order of table
    def getTabInd(self, index):
        if type(index)==str:
            if index in self.mapNames:
                return self.mapNames[index]
            elif index in self._alias:
                return self.getTabInd(self._alias[index])
            else:
                raise Exception('no table named %s' % index)
        return index

    # extract names of table and columns from string
    def extTabCol(self, s):
        tabcols=[]
        for i in range(len(s)-1, -1, -1):
            if s[i]!='.':
                continue
            tab, col=s[0:i], s[(i+1):]
            if tab in self and col in self[tab]:
                tabcols.append((tab, col))

        if len(tabcols)==0:
            raise Exception('wrong format to specify column')
        elif len(tabcols)>1:
            tcInfo=['\t%s %s' % tabcol for tabcol in tabcols]
            tcInfo='\n'.join(tcInfo)
            raise Exception('ambiguous format. Found:\n'+tcInfo)
        return tabcols[0]

    # select specified columns
    # cols: tuple/list/str
    #     tuple: return list
    #     list: return list
    #     str: e.g. 'tab1.col1, tab2.col2' or 'tab.col'
    #         comma-separated: return Data type
    #             comma in the end of string would be ignored
    #         no comma: return a list
    #             a special format: 'tab.col ,': return Data type
    #             simulating syntax of tuple:
    #                 e.g. (a, ) vs. (a)
    def parseSelect(self, cols):
        if type(cols)==tuple:
            return cols
        elif type(cols)==str:
            s=cols.strip()
            if s.find(',')==-1:
                return self.extTabCol(s)
            else:
                cols=s.split(',')
                if cols[-1]=='':
                    del cols[-1]
                tabcols=[]
                for c in cols:
                    c=c.strip()
                    tabcols.append(self.extTabCol(c))
                return tabcols
        elif type(cols)==list:
            return listFlat([self.parseSelect(i)
                                 for i in cols],
                            skipTuple=True)
        else:
            raise Exception('wrong type for select')

    def select(self, tabcols, asName=''):
        cols=self.parseSelect(tabcols)
        if type(cols)==tuple:
            return self[cols[0]].select(cols[1])

        # collected adjecent cols in the same table
        tabcols=[(cols[0][0], [cols[0][1]])]
        for col in cols[1:]:
            if col[0]==tabcols[-1][0]:
                tabcols[-1][1].append(col[1])
            else:
                tabcols.append((col[0], [col[1]]))

        r=DataBase()
        for tab, cols in tabcols:
            r.tables.append(self[tab].select(cols, pkey=True))

        return r.mergeAll(asName=asName, uniqCol=True)

    # merge all tables
    def mergeAll(self, asName='',
                       wrap=False, wrapper=None,
                       uniqCol=False):
        '''
        only depend on property--tables

        wrap: None/str/callable
            str: must be able used in wrap % (tab, col)
            callable: wrap(tab, col), return string
        '''
        result=self.tables[0].copy(name=asName)

        if wrap or wrapper!=None:
            wrapper=keyWrap(wrapper, sep='_')
            result.wrapColName(partial(wrapper,
                                       self.tables[0].name))
            for t in self.tables[1:]:
                result.extend(t, wrap2=partial(wrapper,
                                               t.name))
        else:
            for t in self.tables[1:]:
                result.extend(t)

        if uniqCol:
            result.uniqColName()

        return result

    # visualization
    def plotScatter(self, xCols, yCols,
                          xWraps=None,
                          yWraps=None):
        '''
        x/yCols, x/yWraps:
            determine cols to plot scatter graphic
            like fwrap/wrap in __init__

            column is determined
                through table name and column name
                which are then joined with '.'
            e.g.
                table1.col1 ==> Column col1 in Table table1
        '''
        pass

