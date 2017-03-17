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
import re
import math

from .data import Data
from .toolKit import keyWrap, \
                     listFlat, listBroadCast, \
                     toRePattern
from .SQLKit import _markAS, checkName
from .plot import Plot

class DataBase:
    # supported function used in selection
    SQLFunc={
        'pi': math.pi,
        'e': math.e,
        'sqrt': math.sqrt,
        'hypot': math.hypot,  # hypot(a,b)=sqrt(a**2+b**2)
        'log': math.log,  #log(x[, base])
        'exp': math.exp,
        'pow': math.pow,
        'sin': math.sin,
        'cos': math.cos,
        'tan': math.tan,
        'asin': math.asin,
        'acos': math.acos,
        'atan': math.atan,
        'degrees': math.degrees,
        'radians': math.radians,
        '_markAS': _markAS,
    }

    # __init__
    def __init__(self, fnames=None,
                       tables=None,
                       pcols=0,   # primary key like SQL
                       wrap=None,
                       fwrap=None,
                       types=None):
        '''
        key: convert each name in format
             real name to store tables is format(name)

             str or function:
             str: e.g. '%ssuffix'
             funcion: e.g. lambda x: '%ssuffix' % x
        fkey: same as key, but act on fname
        types: all have similar type
        '''
        # maintain 2 structures
        self.tables=[]   # real space to store data
        self.mapNames={}  # map from name to order
        # one auxiliary structure
        self._alias={}

        # functions for select
        self.SQLFunc={}

        if fnames!=None:
            self.addFiles(fnames, tables,
                          wrap, fwrap,
                          pcols, types)

    # add mulitply files
    def addFiles(self, fnames, tables=None,
                       wrap=None, fwrap=None,
                       pcols=0, types=None):
        wrap=keyWrap(wrap)
        fwrap=keyWrap(fwrap)

        if tables==None:
            tables=fnames

        if not hasattr(pcols, '__iter__'):
            pcols=[pcols]*len(fnames)

        for fname, table, p in zip(fnames, tables, pcols):
            self.addFile(wrap(table), fwrap(fname),
                         p, types)
    # add one file
    def addFile(self, name, fname, pcol=0, types=None):
        d=Data(fname, name=name, pkey=pcol, types=types)
        return self.addTable(d)

    # add table. If existed, overwrite
    def addTable(self, table):
        name=checkName(table.name)
        if name not in self.mapNames:
            self.mapNames[name]=len(self.tables)
            self.tables.append(table)
        else:
            tableNo=self.mapNames[name]
            self.tables[tableNo]=table
        return self

    # convenient method accessing table
    def __getattr__(self, prop):
        if prop=='tNames':
            # names of table
            return [t.name for t in self.tables]

    '''
    def __getitem__(self, key):
        if type(key)==int or key in self:
            return self.tables[self.getTabInd(key)]
        elif type(key)==str or key.find('.')!=-1:
            return self.select(key)
        else:
            return TypeError('wrong type for DataBase')
    '''
    def __getitem__(self, key):
        return self.tables[self.getTabInd(key)]

    def __contains__(self, member):
        if member in self.mapNames or \
           member in self._alias:
            return True
        return False

    # alias name of table
    def alias(self, name, alias):
        checkName(alias)
        if alias in self:
            raise Exception('table %s exists' % alias)
        self._alias[alias]=name
        return self

    def delalias(self, alias):
        del self._alias[alias]
        return self

    def aliasClear(self):
        self._alias.clear()
        return self

    # register function for select
    def regFunc(self, name, func):
        self.SQLFunc[name]=func
        return self

    def delFunc(self, name):
        del self.SQLFunc[name]
        return self

    def clearFunc(self):
        self.SQLFunc.clear()
        return self

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

    # return Data type
    def getTab(self, index):
        return self.tables[self.getTabInd(index)]

    # extract names of table and columns from string
    # when more than one comma exist, try all combinations
    def extTabCol(self, s):
        tab, col=s.split('.')
        if tab not in self:
            raise Exception('tab %s not exist' % tab)
        if col not in self.getTab(tab):
            raise Exception('col %s not exist' % col)
        return tab, col

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
            return cols, None, None
        elif type(cols)==str:
            s=cols.strip()
            asData=True
            if s.find(',')==-1:
                asData=False

            cols, lineFunc, HeadFunc=self.SQLparser(s)

            tabcols=[]
            for c in cols:
                tabcols.append(self.extTabCol(c))

            if not asData:
                tabcols=tabcols[0]
            return tabcols, lineFunc, HeadFunc
        #elif type(cols)==list:
        #    return listFlat([self.parseSelect(i)
        #                         for i in cols],
        #                    skipTuple=True)
        else:
            raise Exception('wrong type for select')

    def select(self, tabcols, asName=''):
        cols, lineFunc, HeadFunc=self.parseSelect(tabcols)
        if type(cols)==tuple:
            return self[cols[0]].select(cols[1])

        # collected adjecent cols in the same table
        lencols=len(cols)
        tabcols=[(cols[0][0], [cols[0][1]])]
        for col in cols[1:]:
            if col[0]==tabcols[-1][0]:
                tabcols[-1][1].append(col[1])
            else:
                tabcols.append((col[0], [col[1]]))

        r=DataBase()
        for tab, cols in tabcols:
            r.tables.append(self[tab].select(cols, pkey=True))

        r=r.mergeAll(asName=asName)

        if lineFunc!=None:
            # whether add primary key: yes=1, no=0
            pkey=len(r.head)-lencols

            # handle head
            ## handle as syntax
            headAs=HeadFunc(*r.body[0][pkey:])
            head=[]
            for h in headAs:
                if type(h)!=_markAS:
                    head.append('')
                elif h.copy:
                    head[-1]=r.head[h.name+pkey]
                else:
                    head[-1]=checkName(h.name)
            ## handle empty head name
            coln=0
            for i, h in enumerate(head):
                if not h:
                    head[i]='col%i' % coln
                    coln+=1
            r.head[pkey:]=head

            # handle body
            for line in r.body:
                line[pkey:]=lineFunc(*line[pkey:])

            # handle types
            r.types=r.getBodyTypes()

        r.uniqColName()

        return r

    ## more complicated SQL syntax parser
    ##    mainly operation on columns and 'as'
    ## what we use is applying function eval
    def SQLparser(self, s):
        tabcols=self.tabColNames()
        tcStr='|'.join(toRePattern(tabcols))
        tcRe=re.compile(r'(%s)' % tcStr)
        cols=tcRe.findall(s)

        # check whether we need to do complex parse
        tcClean=tcRe.sub('', s)
        tcClean=re.sub(r'[ ,]', '', tcClean)
        if not tcClean:
            return cols, None, None

        cols=list(set(cols))

        # replace tabcol with a temporary name
        for i, col in enumerate(cols):
            s=s.replace(col, 'var%i' % i)

        # handle as
        asRe=re.compile(r'\bas\s+([\w_][\w_\d]*)\s*(,|$)')
        if asRe.search(s):
            hds=asRe.sub(r', _markAS("\1")\2', s)
            s=asRe.sub(r',', s) # remove as
        else:
            hds=s

        # find simple query.
        # support any brackets around it
        fields=[]
        varRe=re.compile(r'var(\d+)')
        numQuote=0
        for q in hds.split(','):
            q=q.strip()
            if numQuote<0:
                raise Exception('wrong format for select')
            if numQuote or\
               q.count('(') != q.count(')'):
                fields.append(q)
                numQuote+=q.count('(')-q.count(')')
                continue
            varAll=varRe.findall(q)
            if len(varAll)!=1:
                fields.append(q)
            else:
                qclean=q.replace(' ','')
                q1, i, q2=varRe.split(qclean)
                q1clean=q1.replace('(','')
                q2clean=q2.replace(')','')
                if not q1clean and not q2clean and\
                   q1.count('(')==q2.count(')'):
                    fields.append('var%s' % i)
                    fields.append('_markAS(%s, copy=1)' % i)
                else:
                    fields.append(q)
        hds=', '.join(fields)

        # eval to get function
        lineFunc=self._eval(s, len(cols))
        HeadFunc=self._eval(hds, len(cols))
        return cols, lineFunc, HeadFunc

    def _eval(self, src, argc, wrap='var%i'):
        '''
        convert expression to lambda string
        '''
        wrap=keyWrap(wrap)
        # args string
        args=', '.join([wrap(i) for i in range(argc)])
        # use default kwargs to store local function
        locargs=', '.join(['{0}={0}'.format(i)
                                for i in self.SQLFunc.keys()])
        # when no local
        #     ',' in the end of args is like in tuple
        lambdastr='lambda %s, %s: [%s]' % (args, locargs, src)

        return eval(lambdastr, DataBase.SQLFunc, self.SQLFunc)

    # all valid join of table and column
    def tabColNames(self):
        result=[]
        tNames=list(self.mapNames.keys())+\
               list(self._alias.keys())
        for tname in tNames:
            tab=self.getTab(tname)
            tcformat='%s.%%s' % tname
            for cname in tab.head:
                result.append(tcformat % cname)
        return result

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
        checkName(asName)

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
    def plot(self, xcols, ycols, *args,
                   #xecols=None, yecols=None,
                   wrap=None, ewrap=None,
                   xwrap=None, ywrap=None,
                   xewrap=None, yewrap=None,
                   notDB='',
                   multip=True, nRowCol=None,
                   sameSample=False,
                   **kwargs):
        '''
        wrap: default wrap if x/y/xe/yewrap is None
        ewrap: default wrap for xe/yewrap
        xe/yecols: bool/iterable
            collected in args/kwargs
            if bool: true, same as x/ycols
        x/ycols, x/ywrap:
            determine cols to plot scatter graphic
            like fwrap/wrap in __init__

            column is determined
                through table name and column name
                which are then joined with '.'
            e.g.
                table1.col1 ==> Column col1 in Table table1
        notDB: string
            should only contain 'xc', 'yc', 'xe', 'ye'
            show whether x/y/xe/ye use given data,
                not DataBase data
        sameSample: bool
            if true, all subplots correspoind to same sample
        '''
        # handle xe/yecols
        for k in kwargs:
            if k not in ['xecols', 'yecols']:
                raise Exception('unexpected argument [%s]' % k)
        if len(args)==1:
            xecols=args[0]
            if 'xecols' in kwargs:
                raise TypeError('plot() '+
                                'got multiple values '+
                                'for argument [xecols]')
            if 'yecols' in kwargs:
                yecols=kwargs['yecols']
            else:
                yecols=args[0]
        elif len(args)>1:
            xecols, yecols=args
            if len(kwargs)!=0:
                argnames=', '.join(kwargs.keys())
                raise TypeError('plot() '+
                                'got multiple values '+
                                'for argument [%s]' %
                                argnames)

        else:
            xecols=yecols=None
            if 'xecols' in kwargs:
                xecols=kwargs['xecols']
            if 'yecols' in kwargs:
                yecols=kwargs['yecols']

        # start main work
        datas=[]
        useDB=[]
        wraps=[xwrap, ywrap, xewrap, yewrap]
        xycols=[xcols, ycols, xecols, yecols]
        dbmark=['xc', 'yc', 'xe', 'ye']

        # handle bool type xe/yecols
        for i in range(2, 4):
            if type(xycols[i])==bool:
                if xycols[i]:
                    xycols[i]=xycols[i-2]
                else:
                    xycols[i]=None

        # default wrap
        if ewrap!=None:
            for i in range(2, 4):
                if wraps[i]==None:
                    wraps[i]=ewrap
        if wrap!=None:
            for i in range(4):
                if wraps[i]==None:
                    wraps[i]=wrap

        # exert wrap
        for i in range(4):
            s, w, cols=dbmark[i], wraps[i], xycols[i]
            if cols!=None and s not in notDB:
                if w!=None:
                    w=keyWrap(w)
                    cols=[w(c) for c in cols]
                useDB.append(i)
            datas.append(cols)

        if not useDB:
            return Plot(*datas, multip=multip, nRowCol=nRowCol)

        # match data from database using pkey
        dbcols=[datas[i] for i in useDB]
        if sameSample:
            dbcols=[[i] for i in listFlat(dbcols)]
        else:
            listBroadCast(dbcols)

        DBdatas=[]
        for cols in zip(*dbcols):
            l=len(cols)
            strcols=', '.join(cols)
            datacol=self.select(strcols).toColList()
            DBdatas.append(datacol[-l:])

        if sameSample:
            indnow=0
            DBdatas=DBdatas[0]
            # data used to replace corresponding in datas
            repData=[]
            for i in useDB:
                l=len(datas[i])
                repData.append(DBdatas[indnow:(indnow+l)])
                indnow+=l
        else:
            repData=zip(*DBdatas)

        for i, xydata in zip(useDB, repData):
            datas[i]=list(xydata)

        return Plot(*datas, multip=multip, nRowCol=nRowCol)
