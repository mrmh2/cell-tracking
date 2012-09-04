#!/usr/bin/env python2.7

import os
import sys
import pprint
import random

import numpy as np

import celldata
from celldata import Coords2D
import lnumbers

def shades_of_jop():
    c1 = random.randint(127, 255) 
    c2 = random.randint(0, 127) 
    c3 = random.randint(0, 255) 

    #l = [c1, c2, c3]

    return tuple(random.sample([c1, c2, c3], 3))

def draw_single_vector(array, vfrom, vdisp):
    xf, yf = vfrom
    vx, vy = vdisp

    step = int(abs(vdisp))

    for i in range(0, step):
        r = i * 255
        g = 0
        b =  255 - (i * 255 / step)
        c = (r, g, b)
        px, py = xf + i * vx / step, yf + i * vy / step
        array[px, py] = c
        array[px-1, py] = c
        array[px+1, py] = c
        array[px, py-1] = c
        array[px, py+1] = c

class MatchData():

    def set_displacement(self, v):
        self.displacement = v

    def get_average_v(self):
        displacements = [t.centroid() - f.centroid() for f, t in self.itermatches()]
        return sum(displacements, Coords2D((0, 0))) / len(displacements)
            
    def match_on_restricted_l(self, d_max, v):
        ml = {}
        #cids = self.cdfrom
        for cid, cell in self.cdfrom:
            # TODO - error handling should be further down the stack
            try:
                best_m = self.best_matches_on_l(cid, 15)
            except KeyError:
                best_m = ([], []) 
            fcent = self.cdfrom[cid].centroid()
            adjusted_centroid = fcent + v
            for tocid, candidate in best_m:
                d = adjusted_centroid.dist(candidate.centroid())
                if d < d_max:
                    ml[cid] = tocid
        self.current_ml = ml

    def itermatches(self):
        for cidfrom, cidto in self.current_ml.iteritems():
            yield self.cdfrom[cidfrom], self.cdto[cidto]

    def update_displacement_array(self):
        xdim, ydim = self.centroid_array.shape
        self.displacement_array = np.empty([xdim, ydim], dtype=np.object)
        posdisp = [(f.centroid(), t.centroid() - f.centroid()) for f, t in self.itermatches()]
        for vpos, vdisp in posdisp:
            x, y = vpos
            self.displacement_array[x, y] = vdisp
        self.hasdarray = True

        #sys.exit(0)
#        self.displacement_array = np.zeros([xdim, ydim, 2], dtype=np.int16)
#        posdisp = [(f.centroid(), t.centroid() - f.centroid()) for f, t in self.itermatches()]
#
#        for vpos, vdisp in posdisp:
#            x, y = vpos
#            xd, yd = vdisp
#            self.displacement_array[x, y] = (xd, yd)

    def get_displacement_a(self, p):

        if not self.hasdarray:
            return self.displacement
        x, y = p

        sr = 70

        search_array = self.displacement_array[x-sr:x+sr, y-sr:y+sr]

        values = search_array[np.nonzero(search_array)]
        if len(values):
            return sum(values, Coords2D((0, 0))) / len(values)
        else:
            return Coords2D((0, 0))

    def match_with_displacement_field(self, d):
        ml = {}

        lm = 0.8
        um = 1.3

        for cid, fromcell in self.cdfrom:
            fcent = fromcell.centroid()
            #print "Attempting match for %d, at (%d, %d)" % (cid, fcent.x, fcent.y)
            v = self.get_displacement_a(fcent)
            #print "Local displacement is", v
            cs = self.find_centroid(fromcell.centroid(), v, d)
            if cs != -1:
                candidate = self.cdto[cs]
                #print "Areas:", fromcell.area, candidate.area
                if candidate.area > lm * fromcell.area and candidate.area < um * fromcell.area:
                    ml[cid] = cs
    
        self.current_ml = ml
        self.update_displacement_array()

#    def match_on_centroids_with_area(self, d):
#        v = self.displacement
#
#        ml = {}
#
#        lm = 0.9
#        um = 1.2
#
#        # TODO - should filter by area on a list, not best match (or worst, first)
#        for cid, fromcell in self.cdfrom:
#            cs = self.find_centroid(fromcell.centroid(), v, d)
#            if cs != -1:
#                candidate = self.cdto[cs]
#                #print "Areas:", fromcell.area, candidate.area
#                if candidate.area > lm * fromcell.area and candidate.area < um * fromcell.area:
#                    ml[cid] = cs
#
#        self.current_ml = ml

    def build_centroid_array(self):
        centroids = [cell.centroid().astuple() for cid, cell in self.cdto]
        xs, ys = zip(*centroids)
        xdim, ydim = max(xs) + 1, max(ys) + 1
        self.centroid_array = np.zeros([xdim, ydim], dtype=np.uint32)
        for (cid, cell) in self.cdto:
            self.centroid_array[cell.centroid().astuple()] = cid

    def find_centroid(self, p, v, d):
        cs = self.find_centroids_in_region(p, v, d)

        try:
            return cs[0]
        except IndexError:
            return -1

    def find_centroids_in_region(self, p, s, sr):
        #s = p + celldata.Coords2D((9, -38))
        #print "Looking at:", p, s
        sx, sy = p + s
        #print "Slice around", sx, sy
        subarray = self.centroid_array[sx-sr:sx+sr, sy-sr:sy+sr]
        
        try:
            cs = [int(x) for x in np.nditer(subarray) if x != 0]
        except ValueError:
            return []

        return cs
    
    def __init__(self, celldata_from, celldata_to):
        self.cdfrom = celldata_from
        self.cdto = celldata_to

        ld1 = self.cdfrom.get_lnumbers()
        ld2 = self.cdto.get_lnumbers()

        self.build_centroid_array()
        self.lmatrix = lnumbers.make_matrix(ld1, ld2, lnumbers.weight_contrib)

        self.hasdarray = False

        for cid, cell in celldata_from:
            cell.color = shades_of_jop()

    def best_matches_on_l(self, cid, n):
        cids = lnumbers.best_matches(self.lmatrix[cid], n)
        candidates = [self.cdto[c] for c in cids]
        return zip(cids, candidates)

def main():
    #try:
    #    image_file1 = sys.argv[1]
    #    image_file2 = sys.argv[2]
    #except:
    #    print "Usage %s image_file1 image_file2" % os.path.basename(sys.argv[0])
    #    sys.exit(0)

    ifile1 = 'data/newexp/segmented_image/T05.png'
    ifile2 = 'data/newexp/segmented_image/T06.png'
    lfile1 = 'data/newexp/l_numbers/T05.txt'
    lfile2 = 'data/newexp/l_numbers/T06.txt'

    celldata1 = celldata.CellData(ifile1, lfile1)
    celldata2 = celldata.CellData(ifile2, lfile2)

    md = MatchData(celldata1, celldata2)

    print md.best_matches_on_l(15, 1)

if __name__ == '__main__':
    main()
