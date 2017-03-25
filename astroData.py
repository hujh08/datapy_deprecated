#!/usr/bin/env python3

'''
special format Data used in astronomy.

it could be created from fits binary table.
Meanwile, it's often too huge to be a normal Data.
And so it's unchangeable

the class also provides methods to extract fractional information
    to normal Data type

different from normal Data:
    1, body is fits.fitsrec.FITS_rec,
        like numpy.recarray
    2, types is fortran format and is a list
'''

from astropy.io import fits
import numpy as np
from numpy import sqrt,\
                  pi, deg2rad, cos, sin, arcsin
from math import floor

from .data import Data
from .toolKit import ndList
from .astroKit import spDist, angle2Dist

class astroData:
    def __init__(self, fitsname, extension=None,
                       toquery=True, ngroup=1600):
        with fits.open(fitsname) as hdus:
            if extension==None:
                for hdu in hdus:
                    if type(hdu.data)==fits.fitsrec.FITS_rec:
                        break
            else:
                hdu=hdus[extension]
            fdata=hdu.data

            fcols=fdata.columns

            self.body=fdata
            self.head=fcols.names
            self.types=fcols.formats
            self.len=fdata.shape[0]

            # special property for astronomy
            ## ra, dec
            self.ras=fdata['ra']
            self.decs=fdata['dec']
            self.radecs=np.c_[#np.indices(self.ras.shape[0]),
                              self.ras,
                              self.decs]

            # convert to fast query system if set true
            if toquery:
                self.initQuery(ngroup=ngroup)

    # convert the database to a fast query system
    #     in which return nearest objid
    #         for given ra, dec and search radius
    def initQuery(self, initFunc=None, ngroup=400):
        '''
        initFunc: function to initial system
            it's called using spFunc(ras, decs, ngroup)
                in which ras, decs are both numpy.ndarray
            it should return 
                1, some type of container
                    which stores groups, each filled with indices
                2, function used to get index of container
                    from specified ra, dec
                3, function used to get possible groups' indices
                    from specified ra, dec and search radius
        '''
        if initFunc==None:
            initFunc=self._skySplit
        
        self.indgf, self.groupsf, self.groups=\
            initFunc(self.ras, self.decs, ngroup)

    # function used for query
    ## given ra, dec, get nearest object's id
    def getNearestId(self, ra, dec, radius=5):
        '''
        radius: in unit of arcsec
        getGroupsF:
            function to get list of index of possible groups
        '''
        # to unit of degree
        radius_deg=radius/3600
        maxdist=angle2Dist(radius_deg)

        pIds=[] # possible index
        for indg in self.groupsf(ra, dec, radius):
            pIds.extend(self.groups[indg])

        if not pIds:
            return None

        radecs=np.empty((len(pIds), 2))
        for ir, objid in enumerate(pIds):
            radecs[ir]=self.radecs[objid]

        npdistf=lambda line, radec=(ra, dec):\
                    spDist(radec, line)
        dists=np.apply_along_axis(npdistf, 1, radecs)

        nearIdIndists=dists.argmin()

        if dists[nearIdIndists]<=maxdist:
            return pIds[nearIdIndists]
        else:
            return None

    # get information of nearest objects
    def getNearestInfo(self, ra, dec, query,
                             radius=5):
        '''
        infos: comma-seperated string or list/tuple
            specify which field to extract
            it seems query is case-ignorance
                which is due to recarray
        '''
        nearestId=self.getNearestId(ra, dec, radius)
        if nearestId!=None:
            obj=self.body[nearestId]
            result=[]

            if type(query)==str:
                query=[s.strip() for s in query.split(',')]

            for s in query:
                val=obj[s]
                if type(val)==np.ndarray:
                    val=list(val)
                elif 'float' in type(val).__name__[:5]:
                    val=float(val)
                elif 'int' in type(val).__name__[:5]:
                    val=int(val)
                result.append(val)
            return result
        else:
            return []

    # given Data type, extract information
    def dataQuery(self, rdData, query,
                        radius=5, rdInd=['ra', 'dec'],
                        asName=''):
        '''
        rdInd: indices for ra,dec in rdData
        '''
        # convert to integer indices
        rdInd=[rdData.getColInd(i) for i in rdInd]

        result=Data(name=asName)
        # handle head
        pkey=rdData.pkey
        head=[rdData.head[pkey]]
        if type(query)==str:
            query=[s.strip() for s in query.split(',')]
        head.extend(query)
        result.head=head

        # handle data
        for line in rdData.body:
            ra=line[rdInd[0]]
            dec=line[rdInd[1]]

            info=self.getNearestInfo(ra, dec,
                                     query, radius)
            if info:
                info.insert(0, line[pkey])
                result.body.append(info)

        result.types=result.getBodyTypes()
        return result

    def getNearestId0(self, ra, dec, radius=5):
        '''
        getGroupsF:
            function to get list of index of possible groups
        '''
        npdist=lambda line, radec=(ra, dec): spDist(radec, line)
        dists=np.apply_along_axis(npdist, 1, self.radecs)
        radius_cos=cos(deg2rad(radius/3600))
        indices=np.arange(self.len)[dists>radius_cos]
        print(indices.shape)
        print(dists.argmin())


    # split to different sky region using ra dec
    #     in order to match object fast
    ## default split,
    ##     return index of object with coordinate ra, dec
    def _skySplit(self, ras, decs, ngroup=400):
        minra=ras.min()
        mindec=decs.min()
        if type(ngroup)==list or type(ngroup)==tuple:
            nra, ndec=ngroup
        elif type(ngroup)==int:
            nra=int(sqrt(ngroup))
            ndec=int(ngroup/nra)

        maxra=ras.max()
        maxdec=decs.max()

        dra=(maxra-minra)/nra
        ddec=(maxdec-mindec)/ndec

        # modify dra/ddec to
        #    avoid maxtra/maxdec's index is out of range
        #        i.e. nra
        gap=360-maxra
        if gap<dra:
            dra=gap
        dra=(maxra+0.1*dra-minra)/nra
        gap=90-maxdec
        if gap<ddec:
            ddec=gap
        ddec=(maxdec+0.1*ddec-mindec)/ndec

        container=ndList(nra, ndec)
        indf=lambda ra, dec: (floor((ra-minra)/dra),
                              floor((dec-mindec)/ddec))
        for i, (ra, dec) in enumerate(zip(ras, decs)):
            container.fill(indf(ra, dec), i)

        groupsf=lambda ra, dec, radius: \
                    self._getGroups(ra, dec,
                                    indf, container,
                                    radius)
        return indf, groupsf, container

    # default function to get possible groups
    def _getGroups(self, ra, dec, indf, groups,
                         radius=5):
        '''
        ra: must be 0<=ra<360
        dec: -90<=dec<=90
        indf: callable
            function to calculate index of group for given ra,dec
        radius: float
            search radius in unit of arcsec
        ignore object around the polar, i.e. dec=+/-90
        '''
        # convert to unit degree
        tol_deg=radius/3600
        tol_pi=tol_deg*pi/180

        tol_sin2=sin(tol_pi/2)
        # use (1-cos(tol))/2 as the criterion
        #     since radius is so small
        tol_cos_1=tol_sin2**2

        dec_pi=dec*pi/180
        dec_cos=cos(dec_pi)

        # get possible region: (ra0 ra1 dec0 dec1)
        ## about its algorithm, see readme.md
        dec0=dec-tol_deg
        dec1=dec+tol_deg

        dec0_pi=dec0*pi/180
        dec0_cos=cos(dec0_pi)
        dec1_pi=dec1*pi/180
        dec1_cos=cos(dec1_pi)

        cosdmin=min(dec0_cos, dec1_cos)

        # sin^2((r-r0)/2)
        sqsin_d2=tol_cos_1/(dec_cos*cosdmin)
        sin_d2=sqrt(sqsin_d2)
        tolr_deg=arcsin(sin_d2)*2*180/pi

        ra0=ra-tolr_deg
        ra1=ra+tolr_deg
        if ra0<0:
            ra0+=360
        if ra1>=360:
            ra1-=360

        # corresponding index
        indra0, indec0=indf(ra0, dec0)
        indra1, indec1=indf(ra1, dec1)

        nra, ndec=groups.shape
        if indra0>indra1:
            # span ra=0
            indras=list(range(indra0, nra))
            indras.extend(list(range(0, indra1+1)))
            if not indras:
                return []
        else:
            if indra0<0:
                indra0=0
            if indra1>=nra:
                indra1=nra-1

            if indra0>=nra or indra1<0:
                return []
            indras=range(indra0, indra1+1)

        if indec0<0:
            indec0=0
        if indec1>=ndec:
            indec1=ndec-1

        # possible groups
        groups_poss=[]
        for indr in indras:
            for inde in range(indec0, indec1+1):
                groups_poss.append((indr, inde))
        return groups_poss
