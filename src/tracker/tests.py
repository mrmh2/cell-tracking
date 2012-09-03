#!/usr/bin/env python2.7

import sys
import pprint

import bb
import lnumbers
import celldata
import matchdata

def test_contains(myb, (x, y)):
    print "Testing if bb contains %d,%d:" % (x, y), myb.contains((x, y))

def test_bb():
    myb = bb.BoundingBox((10, 10), (100, 100))
    
    for x in range(0, 121, 60):
        for y in range(0, 121, 60):
            test_contains(myb, (x, y))


    # TODO - edge cases (literally!)

def test_l():
    ln = lnumbers.parse_l_file('data/newexp/l_numbers/T06.txt')

    pprint.pprint(ln)

def test_for_ls(image_file, l_file):

    ln = lnumbers.parse_l_file(l_file)
    cd = celldata.CellData(image_file)

    lkeys = set(ln.keys())
    ckeys = set(cd.keys())

    unique_to_l = list((lkeys | ckeys) - ckeys)
    unique_to_c = list((lkeys | ckeys) - lkeys)

    if len(unique_to_c) or len(unique_to_l):
        print "For %s/%s" % (image_file, l_file)
        if len(unique_to_c):
            print "    Unique to data from image file:", unique_to_c
        if len(unique_to_l):
            print "    Unique to data from l file:", unique_to_l

def test_l_match(expname):
    sys.path.insert(0, '/Users/hartleym/local/python')
    import get_data_files as gdf

    d = gdf.get_data_files(expname)
    dps = []
    for dp in sorted(d.iteritems()):
        name, vd = dp
        a = [vd['Segmented image'], vd['L numbers']]
        dps.append(a)

    for dp in dps[5:6]:
        test_for_ls(dp[0], dp[1])
   
def test_coords_2D():
    p1 = celldata.Coords2D((1, 2))
    p2 = celldata.Coords2D((4, 6))

    print p1 * p2

    print abs(p1)

    print p1.dist(p2)

def test_matchdata():
    ifile1 = 'data/newexp/segmented_image/T05.png'
    ifile2 = 'data/newexp/segmented_image/T06.png'
    lfile1 = 'data/newexp/l_numbers/T05.txt'
    lfile2 = 'data/newexp/l_numbers/T06.txt'

    celldata1 = celldata.CellData(ifile1, lfile1)
    celldata2 = celldata.CellData(ifile2, lfile2)

    md = matchdata.MatchData(celldata1, celldata2)

    cid1 = 374
    cid2 = 511

    from_centroid = md.cdfrom[cid1].centroid()
    to_centroid = md.cdto[cid2].centroid()
    print "Centroid of left cell:", from_centroid
    print "Centroid of right cell:", to_centroid
    tx, ty = from_centroid.astuple()
    #print md.centroid_array[tx, ty]

    c = md.find_centroid(from_centroid)
    print "Centroid match is", c


def main():
    #test_bb()
    #test_l()
    test_l_match('newexp')
    #test_coords_2D()
    #test_matchdata()

if __name__ == '__main__':
    main()
