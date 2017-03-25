#!/usr/bin/env python3

'''
some auxiliary functions/classes used for astroData
'''

from numpy import cos, sin, deg2rad

# gauge of distance of two point in spere
def spDist(radec0, radec1):
    '''
    return -cos(theta)
        theta is the angle between radec0 and radec1
    '''
    d0=deg2rad(radec0[1])
    d1=deg2rad(radec1[1])
    r0mr1=deg2rad(radec0[0]-radec1[0])
    cosd=cos(d0)*cos(d1)*cos(r0mr1)+sin(d0)*sin(d1)
    return -cosd

# convert theta to former distance gauge
def angle2Dist(deg):
    return -cos(deg2rad(deg))