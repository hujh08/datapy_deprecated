handle text file like DataBase Software

# comment about astroData
## algorithm to get possible sky sections
given a search radius, what we need is possible region definded by
    (ra0 ra1 dec0 dec1)

distance D in sphere of two point (r0, d0) (r, d):
    cos(D)=cosd0*cosd*cos(r-r0)+sind0*sind
          =cos(d-d0)-cosd0*cosd*2*sin^2((r-r0)/2)

for dec
when 180>|d-d0|>tol>0, which means
    cos(d-d0)<cos(tol),
then
    cos(D)<cosd0*cosd+sind0*sind=cos(d-d0)<cos(tol)
so
    D>tol
and then the tolerable range of dec is
    (dec-tol, dec+tol)

for ra
when cosd>cosdmin, then we have
    cos(D)<1-cosd0*cosdmin*2*sin^2((r-r0)/2)
if
    cosd0*cosdmin*2*sin^2((r-r0)/2)>1-cos(tol)
then
    cos(D)<cos(tol)
so when dec is in his tolerance range,
   then tolerable r satisfy
       cosd0*cosdmin*2*sin^2((r-r0)/2)<1-cos(tol)
   where
       cosdmin is min(cos(d0-tol), cos(d0+tol))