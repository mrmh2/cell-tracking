#!/usr/bin/env python2.7

import os
import sys
import pprint
import itertools
import random
from operator import itemgetter

import pygame

import bb
import lnumbers
import celldata
from celldata import Coords2D
import matchdata
from mltools import read_ml
from mutil import mean, sorted_nicely
from matchmaker import get_voxel_spacing

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

def test_read_ml():
    ml = read_ml('T00T01.match')
    pprint.pprint(ml)

def calc_iso_params(cs):
    vdisps = [t - f for f, t in cs]
    vd = sum(vdisps, Coords2D((0, 0))) / len(vdisps)
    adj = [abs(v - vd) for v in vdisps]
    m = min(adj)
    index = [i for i, j in enumerate(adj) if j == m][0]
    center = cs[index][0]

    top = [f - center for f, t in cs]
    bottom = [t - f - vd for f, t in cs]

    xp = zip([x for x, y in top], [x for x, y in bottom])
    xp = xp + zip([y for x, y in top], [y for x, y in bottom])

    s = mean([float(a)/float(b) for a, b in xp])

    return center, vd, s


def test_isoculator():

    myl =   [((336, 623),  (396, 726)),
            ((228, 523),  (276, 598)),
            ((532, 532),  (629, 605)),
            ((224, 249),  (273, 272)),
            ((350, 406),  (411, 455)),
            ((473, 278),  (551, 303)),]

    cs = [(Coords2D(f), Coords2D(t)) for f, t in myl]

    center, vd, s = calc_iso_params(cs)

    print center, vd, s

def load_data(expname, names):
    sys.path.insert(0, os.path.join(os.environ['HOME'], 'local/python'))
    import get_data_files as gdf
    d = gdf.get_data_files(expname)

    dlist = [d[k] for k in sorted_nicely(d.keys())]
    # This is now something of a list incomprehension
    return [[a[n] for n in names if n in a] for a in dlist]

def test_matchdata2():
    expname = 'newexp'
    tp = 5
    names = ['Segmented image', 'L numbers', 'Projection', 'Microscope metadata']
    expdata = load_data(expname, names)

    ifile1, lfile1, pfile1, vfile1 = expdata[tp]
    ifile2, lfile2, pfile2, vfile2 = expdata[tp + 1]
    ml = read_ml('data/newexp/matches/T%02dT%02d.match' % (tp, tp + 1))

    sx1, sy1, sz1 = get_voxel_spacing(vfile1)
    sx2, sy2, sz2 = get_voxel_spacing(vfile2)
  
    celldata1 = celldata.CellData(ifile1, lfile=lfile1)
    celldata2 = celldata.CellData(ifile2, lfile=lfile2, scale=(sx2/sy1, sy2/sy1))
   
    md = matchdata.MatchData(celldata1, celldata2)

    allas = []
    for cid in md.get_loby_candidates():
        bm = md.lmatrix.best_n_matches(cid, 5)
        areas = [float(md.cdto[tid].area)/md.cdfrom[cid].area for tid in bm]
        try:
            real_m = ml[cid]
        except KeyError:
            real_m = []
        print cid
        print bm
        print real_m
        print areas
        for a in areas:
            allas.append(a)

    #print sorted(allas)[len(allas)/2], len(allas)

    pml = {id : md.lmatrix.best_n_matches(id, 5) 
            for id in md.get_loby_candidates()}

    pprint.pprint(pml)

    for fid, tids in pml.iteritems():
        for tid in tids:
            delta_a = float(md.cdto[tid].area) / md.cdfrom[fid].area
            if delta_a < 1.0 or delta_a > 1.7:
                pml[fid].remove(tid)

    pprint.pprint(pml)

    ds = []
    for fid, tids in pml.iteritems():
        for tid in tids:
            ds.append(abs(md.cdto[tid].centroid - md.cdfrom[fid].centroid))

    med_d = sorted(ds)[len(ds)/3]

    for fid, tids in pml.iteritems():
        for tid in tids:
            d = abs(md.cdto[tid].centroid - md.cdfrom[fid].centroid)
            if d > med_d:
                pml[fid].remove(tid)

    pprint.pprint(pml)

    failed = 0
    good = 0
    for fid in pml:
        #print fid,
        try:
            real_m = ml[fid]
        except KeyError:
            real_m = []

        if len(real_m) == 1 and len(pml[fid]):
            if real_m[0] != pml[fid][0]:
                failed +=1
                print 'BAD'
            else:
                good += 1

    print failed, good, float(good) / (failed + good)

    #ml = {fid : pml[fid][:1] for fid in pml}

    ml = md.get_possible_ml()

    s = random.sample(ml, 5)

    sd = {k : ml[k] for k in random.sample(ml, 5)}

    cs = []
    for fid, tids in sd.iteritems():
        fc = md.cdfrom[fid].centroid
        tc = md.cdto[tids[0]].centroid

        cs.append((fc, tc))

    #inp = [(f.centroid, msum([t for t in ts]).centroid )
        #inp = [(f.centroid, msum([t.centroid for t in ts]) )
   #         for f, ts in self.itermatches()]

    center, vd, s = md.calc_iso_params(cs)

    print md.sampled_iso_params()



def test_l_numbers():
    expname = 'newexp'
    tp = 5
    names = ['Segmented image', 'L numbers', 'Projection', 'Microscope metadata']
    expdata = load_data(expname, names)

    ifile1, lfile1, pfile1, vfile1 = expdata[tp]
    ifile2, lfile2, pfile2, vfile2 = expdata[tp + 1]

    celldata1 = celldata.CellData(ifile1, lfile=lfile1)
    #celldata2 = celldata.CellData(ifile2, lfile=lfile2)
    #md = matchdata.MatchData(celldata1, celldata2)
    #print md.lmatrix.best_match(515)
    lm = lnumbers.LMatrix.from_files(lfile1, lfile2)
    #for id, vals in lm.ln1.iteritems():
    #    print id, lm.best_n_matches(id, 5), sum(vals[5:9])

    lobiness = [(id, sum(vals[6:11])) for id, vals in lm.ln1.iteritems()]
    slobi = sorted(lobiness, key=itemgetter(1))
    blobi = slobi[-45:-5]

    ml = read_ml('data/newexp/matches/T%02dT%02d.match' % (tp, tp + 1))

    ts = 0
    for id, score in blobi:
        try:
            real_m = ml[id]
        except KeyError:
            real_m = []
        bm = lm.best_n_matches(id, 5)
        success = False
        for m in real_m:
            if m in bm:
                success = True
                ts += 1

        print id, score, bm, real_m, success

    print ts

    print zip(*blobi)[0]

    #print lobiness

    #print lm.best_match(456)

#    print lm.best_n_matches(515, 3)
#    print lm.best_match(515)
#    m, score = lm.match_with_score(515)
#    print float(celldata1[515].area) / celldata2[m].area
#    print lm.match_with_score(322)
#    m, score = lm.match_with_score(322)
#    print float(celldata1[322].area) / celldata2[m].area
#    print lm.match_with_score(324)
#    m, score = lm.match_with_score(324)
#    print float(celldata1[324].area) / celldata2[m].area

    #print lm[515][515]


def main():
    #test_bb()
    #test_l()
    #test_l_match('newexp')
    #test_coords_2D()
    #test_matchdata()
    test_matchdata2()
    #test_centroid_summer()
    #test_smarter_centroid()
    #ptest()
    #test_overall_centroid()
    #test_read_ml()
    #test_isoculator()
    #test_l_numbers()

if __name__ == '__main__':
    main()
