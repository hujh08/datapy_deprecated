#!/usr/bin/env python3

'''
handle text file
    which is often used to record data
    and has structure as following:
    head: several line started with #
          first line is special which is the name of columns
          the others are some comments
    body: data
          each line has same number of columns
              separated with whitespace
    head and body should not be mixed
    no empty line between them
'''

import sys
import re
# support cmp keyword in sort
from functools import cmp_to_key

from .toolKit import keyWrap,\
                     strDelIn, strInsert,\
                     listFlat
from .SQLKit import checkName

class Data:
    '''
    many method used to change in-place returns self
        in order to allow chain of method
    e.g.
        Data('somefile').setColType(0, 'f')\
                        .setColName(1, 'other')\
                        .copy().sort()
    '''
    def __init__(self, filename=None, types=None,
                       name='',
                       pkey=0):
        '''
        all data is read in as string by default
        pkey: primary key, same role as in database
        '''
        self.pkey=pkey
        self.name=name

        if filename==None:
            self.head=[]
            self.body=[]
            return

        with open(filename) as f:
            # name of columns
            self.head=checkName(f.readline()[1:].split())
            # skip other comment line
            for line in f:
                if line[0]!='#':
                    break

            # fill body
            self.body=[line.split()]
            for line in f:
                self.body.append(line.split())

            # check width of data
            for i, line in enumerate(self.body):
                if len(line)!=len(self.head):
                    raise Exception('File "%s", ' % filename +
                                    'in line %i:\n' % i +
                                    '  mismatch between '+
                                    'head and body')

            self.types='s'*len(self.head)

        if types!=None:
            self.asTypes(types)

    # convenient method to access data
    def __getattr__(self, prop):
        if prop=='len':
            return len(self.body)
        elif prop=='width':
            return len(self.head)

    def __len__(self):
        return self.len

    def __contains__(self, col):
        return col in self.head

    # get number of column giving number/string/None
    def getColInd(self, col=None):
        if col==None:
            return self.pkey
        elif type(col)==str:
            return self.head.index(col)
        return col

    # del column
    def delCol(self, col):
        col=self.getColInd(col)
        del self.head[col]

        for line in self.body:
            del line[col]

        self.types=strDelIn(self.types, col)

    # insert column
    def insertCol(self, clist, index=0,
                        ctype=None, cname=None):
        '''
        ctype: str/callable
            change col to specify format
            or it can be a function to change element in clist
        index: int
            insert new column befor original index column
        cname: str
            if None: 'col'+index
        '''
        if len(clist)!=self.len:
            raise Exception('mismatched length to insert')

        typeNames=set()
        if ctype==str:
            typeNames.add(typeNames)
            ctype=self.parseTypes(ctype)

        if callable(ctype):
            clist=map(ctype, clist)
        elif ctype!=None:
            raise TypeError('ctype must be None/str/callable,'+
                            ' found %s' % type(ctype).__name__)

        # handle body
        for c, line in zip(clist, self.body):
            line.insert(index, c)
            typeNames.add(self.getTypeName(c))

        if len(typeNames)!=1:
            raise Exception('mismatch type of inserted column')

        # handle types
        self.types=strInsert(self.types,
                             typeNames.pop(), index)

        # handle head
        if cname==None:
            cname='col%i' % index

        checkName(cname)

        if type(cname)!=str:
            raise TypeError('head name must be str,'+
                            ' found %s' % type(cname).__name__)

        self.head.insert(index, cname)

        # handle pkey
        if index<=self.pkey:
            self.pkey+=1

        return self

    def appendCol(self, col, *args, **keywords):
        # call insertCol
        return self.insertCol(col, self.width,
                              *args, **keywords)

    # get name of type for a given data
    def getTypeName(self, d):
        if type(d)==int:
            return 'i'
        elif type(d)==float:
            return 'f'
        elif type(d)==str:
            return 's'
        else:
            raise Exception('unsupported type for data')

    # copy
    def copy(self, name=''):
        checkName(name)
        result=Data(name=name, pkey=self.pkey)

        result.head=self.head.copy()

        for line in self.body:
            result.body.append(line.copy())

        result.types=self.types

        return result

    # handle type of data
    def asTypes(self, types):
        '''
        format is a string, e.g. 's', 'sff'
        only support 3 format:
            s: string
            i: integer
            f: float
        special format:
            number after char: show replicated number
                e.g. 's2ff' := 'ssff'
            asterisk: fill up with previous char
                e.g. number of column=4
                     's*f' := 'sssf'
                but there should be only 1 asterisk 
        its length can be different with number of columns
        if it's longer, excess chars are dropped
        if shorter, the last char is used filled the left
        '''
        # parse complicated format
        types=self.parseTypes(types)

        # only convert columns with different type
        convert=[]
        for (i, c0), c in zip(enumerate(self.types), types):
            if c0!=c:
                convert.append((i, self.str2func(c)))

        if not len(convert):
            return self

        for line in self.body:
            for i, f in convert:
                line[i]=f(line[i])

        self.types=types

        return self

    def setColType(self, col, dtype):
        '''
        set type for an column
        '''
        col=self.getColInd(col)

        if self.types[col]==dtype:
            return self
        f=self.str2func(dtype)
        for line in self.body:
            line[col]=f(line[col])

        self.types=self.types[0:col]+dtype+\
                   self.types[(col+1):]

        return self

    def parseTypes(self, types):
        '''
        parse complicated format:
            number after char: show replicated number
                e.g. 's2ff' := 'ssff'
            asterisk: fill up with previous char
                e.g. number of column=4
                     's*f' := 'sssf'
                but there should be only 1 asterisk
        its length can be different with number of columns
        if it's longer, excess chars are dropped
        if shorter, the last char is used filled the left
        '''
        num=len(self.head)

        # support complicated format
        item=r'[sif](?:\*|\d*)'

        if not re.match(r'^(%s)*$' % item, types):
            raise Exception('wrong format for types')

        if types.count('*')>1:
            raise Exception('too many asterisk')

        if re.search(r'\d+', types):
            typesL=[]
            for t in re.findall(item, types):
                if len(t)>1 and t[-1]!='*':
                    t=t[0]*int(t[1:])
                typesL.append(t)
            types=''.join(typesL)

        if types.find('*')!=-1:
            fields=types.split('*')
            if len(types)-2>num:
                types=fields[0][:-1]+fields[1]
            else:
                fill=fields[0][-1]*(num+1-len(types))
                types=fields[0]+fill+fields[1]
        elif len(types)<num:
            types+=types[-1]*(num-len(types))

        types=types[0:num]

        return types

    def str2func(self, dtype):
        '''
        convert string to a convert function
        '''
        if dtype=='s':
            return str
        elif dtype=='i':
            return int
        elif dtype=='f':
            return float
        else:
            raise Exception('unsupported data type')

    # get types of body
    def getBodyTypes(self):
        types=[]
        for c in self.body[0]:
            types.append(self.getTypeName(c))

        return ''.join(types)

    # set name of data
    def setName(self, name):
        checkName(name)
        self.name=name
        return self

    # make head name unique
    def uniqColName(self):
        names={}
        for i, n in enumerate(self.head):
            if n not in names:
                names[n]=0
            else:
                self.head[i]='%s%i' % (n, names[n])
                names[n]+=1
        return self

    # set name of column
    def setColName(self, col, name):
        checkName(name)
        col=self.getColInd(col)
        self.head[col]=name
        return self

    def getWrapColName(self, wrapper=None, skip=None):
        '''
        skip: columns to skip wrapper,
            default: skip self.pkey
            []: wrap all
            [col1, col2, ...]: 
        '''
        if wrapper==None:
            return self.head.copy()

        wrapper=keyWrap(wrapper)
        result=[wrapper(k) for k in self.head]

        if skip==None:
            skip=[self.pkey]  # default
        elif not hasattr(skip, '__iter__'):
            skip=[skip]

        for col in skip:
            col=self.getColInd(col)
            result[col]=self.head[col]

        return result

    def wrapColName(self, wrapper=None, skip=None):
        '''
        call getWrapColName
        change in place
        '''
        if wrapper==None:
            return self

        self.head=self.getWrapColName(wrapper, skip)
        checkName(self.head)
        return self

    # select special column
    # cols: str/int/iterable
    #     int: return list
    #     iterable, not str: return list
    #     str:
    #         comma-separated: return Data type
    #             comma in the end of string would be ignored
    #         no comma: return a list
    #             a special format: 'col ,': return Data type
    #             simulating syntax of tuple:
    #                 e.g. (a, ) vs. (a)
    def parseSelect(self, cols):
        if type(cols)==int:
            return cols
        elif type(cols)==str:
            s=cols.strip()
            if s.find(',')==-1:
                return self.getColInd(s)
            else:
                cols=s.split(',')
                if cols[-1]=='':
                    del cols[-1]
                indices=[]
                for c in cols:
                    c=c.strip()
                    indices.append(self.getColInd(c))
                return indices
        elif hasattr(cols, '__iter__'):
            return listFlat([self.parseSelect(i)
                                 for i in cols])
        else:
            raise Exception('wrong type for select')

    def select(self, cols, asName='', pkey=False):
        '''
        cols: str/int/list/tuple
        pkey: whether or not include primary key
              if true and pkey is not in selected cols
                 add pkey as the 1st column
        '''
        checkName(asName)

        cols=self.parseSelect(cols)
        asList=False
        if type(cols)==int:
            cols=[cols]
            asList=True

        body=[]
        for line in self.body:
            body.append([line[i] for i in cols])

        if asList:
            return listFlat(body)

        result=Data(name=asName)
        result.body=body
        result.head=[self.head[i] for i in cols]
        result.types=''.join([self.types[i] for i in cols])

        # handle pkey
        if self.pkey in cols:
            result.pkey=cols.index(self.pkey)
        elif pkey:
            result.insertCol(self.simpleSelect(),
                             cname=self.head[self.pkey])
            result.pkey=0

        return result

    def simpleSelect(self, col=None):
        '''
        just select one column and return list
        '''
        col=self.getColInd(col)
        return [line[col] for line in self.body]

    # sort lines
    def sort(self, *args, **keywords):
        '''
        sort in-place
        call sortedBody with arguments:
            col: column for sort
            comp: comparing funcion
            reverse: reverse order if True
        '''
        self.body=self.sortedBody(*args, **keywords)

        return self

    def sorted(self, *args, **keywords):
        '''
        return sorted copy
        call sortedBody with arguments:
            col: column for sort
            comp: comparing funcion
            reverse: reverse order if True
        '''
        result=Data()
        result.head=self.head.copy()
        result.body=self.sortedBody(*args, **keywords)
        return result

    def sortedBody(self, col=None, comp=None, reverse=False):
        '''
        return sorted body

        col: column for sort
        comp: comparing funcion
        reverse: reverse order if True
        '''
        col=self.getColInd(col)

        if comp!=None:
            # in python3 cmp keyword is removed entirely
            keyF=lambda l: cmp_to_key(comp)(l[1])
        else:
            keyF=lambda l: l[1]

        body=[]
        for i, c in sorted(enumerate(self.select(col)),
                           key=keyF,
                           reverse=reverse):
            body.append(self.body[i])

        return body

    # filter
    def filter(self, func, cols=0, asName=''):
        result=Data(pkey=self.pkey, name=asName)
        result.head=self.head
        result.types=self.types

        for line in self.body:
            if func(line[cols]):
                self.body.append(line)

        return result

    # reshape of Data
    ## extract column as list
    def toColList(self, cols=None):
        '''
        cols: same as select, but must let select return Data
            return all cols as default
        '''
        data=self.body
        if cols!=None:
            data=self.select(cols, pkey=False).body

        if not data:
            return []

        result=[[] for i in range(len(data[0]))]
        for line in data:
            for i, col in enumerate(line):
                result[i].append(col)

        return result

    ## use dictionary to represent data
    def toDict(self, col=None):
        col=self.getColInd(col)

        result={}
        for line in self.body:
            key=line[col]
            result[key]=line.copy()
            del result[key][col]
        return result

    # extend with another block of data
    def extend(self, data2, col1=None,
                            col2=None,
                            wrap1=None,
                            wrap2=None):
        '''
        col1/2: column to match
        wrap1/2: wrap name of column to avoid replicated name
        '''
        col1=self.getColInd(col1)
        col2=data2.getColInd(col2)

        dataDict2=data2.toDict(col2)

        # join head
        head2=data2.getWrapColName(wrap2, col2)
        del head2[col2]
        checkName(head2)

        self.wrapColName(wrap1, col1)
        self.head.extend(head2)

        # join types
        self.types+=strDelIn(data2.types, col2)

        # line number to be deleted
        body=[]
        for i, line in enumerate(self.body):
            key=line[col1]
            if key in dataDict2:
                line.extend(dataDict2[key])
                body.append(line)

        self.body=body

        return self

    # print function
    def strLines(self, precise=4):
        '''
        precise: for print of float number
        '''
        yield '#'+' '.join(self.head)

        formats=[]
        for f in self.types:
            if f=='f':
                formats.append('%%.%if' % precise)
            else:
                formats.append('%%%s' % f)
        formats=' '.join(formats)

        #print(formats)
        for row in self.body:
            yield formats % tuple(row)

    def write(self, filename=None, precise=4):
        if filename==None:
            f=sys.stdout
        else:
            f=open(filename, 'w')

        for line in self.strLines(precise):
            f.write(line+'\n')

        if filename!=None:
            f.close()