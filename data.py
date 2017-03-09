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

import re
# support cmp keyword in sort
from functools import cmp_to_key

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
                       pkey=0):
        '''
        all data is read in as string by default
        pkey: primary key, same role as in database
        '''
        self.pkey=pkey

        if filename==None:
            self.head=[]
            self.body=[]
            return

        with open(filename) as f:
            # name of columns
            self.head=f.readline()[1:].split()
            # skip other comment line
            for line in f:
                if line[0]!='#':
                    break

            self.body=[line.split()]
            for line in f:
                self.body.append(line.split())

            self.types='s'*len(self.head)

        if types!=None:
            self.asTypes(types)

    # convenient method to access data
    def __getattr__(self, prop):
        if prop=='len':
            return len(self.body)
        elif prop=='width':
            return len(self.head)

    # get number of column giving number/string/None
    def getCol(self, col=None):
        if col==None:
            return self.pkey
        elif type(col)==str:
            return self.head.index(col)
        return col

    # del column
    def delCol(self, col):
        col=self.getCol(col)
        del self.head[col]

        for line in self.body:
            del line[col]

    # copy
    def copy(self):
        result=Data(pkey=self.pkey)

        result.head=self.head.copy()

        for line in self.body:
            result.body.append(line.copy())

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
        col=self.getCol(col)

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

    # set name of column
    def setColName(self, col, name):
        col=self.getCol(col)

        self.head[col]=name

        return self

    # select special column
    def select(self, col):
        col=self.getCol(col)

        result=[]
        for line in self.body:
            result.append(line[col])

        return result

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
        col=self.getCol(col)

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

    # use dictionary to represent data
    def toDict(self, col=None):
        col=self.getCol(col)

        result={}
        for line in self.body:
            key=line[col]
            result[key]=line.copy()
            del result[key][col]
        return result

    # extend with another block of data
    def extend(self, data2, col1=None,
                            col2=None):
        '''
        col1/2: column to match
        '''
        col1=self.getCol(col1)
        col2=data2.getCol(col2)

        dataDict2=data2.toDict(col2)

        head2=data2.head
        del head2[col2]

        self.head.extend(head2)

        # line number to be deleted
        body=[]
        for i, line in enumerate(self.body):
            key=line[col1]
            if key in dataDict2:
                line.extend(dataDict2[key])
                body.append(line)

        self.body=body

        return self