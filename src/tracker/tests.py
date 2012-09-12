#!/usr/bin/env python2.7

import sys
import pprint
import itertools

import pygame

import bb
import lnumbers
import celldata
from celldata import Coords2D
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

def test_single_match(md):
    cid1 = 374
    cid2 = 511
    from_centroid = md.cdfrom[cid1].centroid()
    to_centroid = md.cdto[cid2].centroid()
    print "Centroid of left cell (cid %d):" % cid1, from_centroid
    print "Centroid of right cell (cid %d):"% cid2, to_centroid
    c = md.find_centroid(from_centroid, v, 10)
    print "Centroid match is", c
    v = from_centroid
    # TODO - unit testize
    print md.get_displacement_a(v), to_centroid - from_centroid

    vn = from_centroid + Coords2D((10, 10))
    print md.get_displacement_a(vn)




def test_matchdata():
    ifile1 = 'data/newexp/segmented_image/T05.png'
    ifile2 = 'data/newexp/segmented_image/T06.png'
    lfile1 = 'data/newexp/l_numbers/T05.txt'
    lfile2 = 'data/newexp/l_numbers/T06.txt'

    celldata1 = celldata.CellData(ifile1, lfile1)
    celldata2 = celldata.CellData(ifile2, lfile2)
    del(celldata1[1])
    del(celldata2[1])

    md = matchdata.MatchData(celldata1, celldata2)

    v = celldata.Coords2D((8, -36))
    md.match_on_restricted_l(8, v)
    print "On l, matched:", len(md.current_ml)
    md.set_displacement(v)

    #md.match_on_centroids_with_area(7)
    md.match_with_displacement_field(7)
    print "Initial centroid + area: matched:", len(md.current_ml)
    #pprint.pprint(md.current_ml)

    md.match_with_displacement_field(10)
    print "Local displacement: matched:", len(md.current_ml), "of", len(md.cdfrom)

    md.match_with_displacement_field(10)
    print "Local displacement: matched:", len(md.current_ml), "of", len(md.cdfrom)

    md.match_with_displacement_field(10)
    print "Local displacement: matched:", len(md.current_ml), "of", len(md.cdfrom)

    test_divide_tracker(md)

def check_divide(md, cid, v):

    ll = 0.8
    ul = 1.2

    xd, yd = v
    to_cids = []
    for x, y in md.cdfrom[cid]:
        try:  
            c = md.centroid_array[x + xd, y + yd]
        except IndexError:
            pass
        if c != 0:
            to_cids.append(c)

    # TODO - consider all sets of 2
    if len(to_cids) == 2:
        fa = md.cdfrom[cid].area
        ta = md.cdto[to_cids[0]].area + md.cdto[to_cids[1]].area
        r = float(ta) / float(fa)
        if r > ll and r < ul:
            print "I think %d -> %d, %d" % (cid, to_cids[0], to_cids[1])

    #i = md.iterunmatched()
#
#    for a in i:
#        print a

def test_centroid_summer():
    ifile = 'data/newexp/segmented_image/T05.png'
    cd = celldata.CellData(ifile)

    cells = [cd[150], cd[151], cd[152]]

    for c in cells:
        print c.centroid()

    #print cells[0].pl + cells[1].pl

    tpl = sum([c.pl for c in cells], [])
    xs, ys = zip(*tpl)
    x, y = sum(xs) / len(tpl), sum(ys) / len(tpl)
    print Coords2D((x, y))

    #newcell = cells[0] + cells[1] + cells[2]
    newcell = sum(cells, celldata.Cell([]))
    print newcell.centroid()

def test_overall_centroid():
    ifile = 'data/newexp/segmented_image/T00.png'
    ifile2 = 'data/newexp/segmented_image/T01.png'
    cd = celldata.CellData(ifile)
    cd2 = celldata.CellData(ifile2)
    print "Loaded celldata"
    sys.stdout.flush()

    #all = sum(cd.cells, celldata.Cell([]))

    #allpl = [c.pl for c in cd.cells]

    #myl = list(itertools.chain.from_iterable(allpl))

    #xs, ys = zip(*myl)

    #print sum(xs) / len(xs), sum(ys) / len(ys)
    print cd.center
    print cd2.center


def test_divide_tracker(md):
#    v = celldata.Coords2D((8, -36))

 #   for cid, cell in md.iterunmatched():
    # 172
  #      md.check_divide(cid)
    md.get_divided_cells()
    pprint.pprint(md.divisions)

def test_smarter_centroid():
    ifile = 'data/newexp/segmented_image/T05.png'
    cd = celldata.CellData(ifile)

    print cd[150].centroid

def ptest():
    pygame.init()
    vinfo = pygame.display.Info()
    xdim = int(vinfo.current_w * 0.9)
    ydim = int(vinfo.current_h * 0.9)
    window = pygame.display.set_mode((xdim, ydim))
    pygame.display.set_caption("test")
    screen = pygame.display.get_surface()
    print screen.get_masks()
    ifile = 'data/newexp/segmented_image/T05.png'
    imgsurface = pygame.image.load(ifile)
 
    print imgsurface.get_masks()
    print imgsurface.get_shifts()
    

def main():
    #test_bb()
    #test_l()
    #test_l_match('newexp')
    #test_coords_2D()
    #test_matchdata()
    #test_centroid_summer()
    #test_smarter_centroid()
    #ptest()
    test_overall_centroid()

if __name__ == '__main__':
    main()
