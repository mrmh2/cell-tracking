#!/usr/bin/env python2.7

import os
import sys
import pprint

import numpy as np

import celldata
import lnumbers

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
    def match_on_restricted_l(self, d_max, v):
        ml = {}
        #cids = self.cdfrom
        for cid, cell in self.cdfrom:
            # TODO - error handling should be further down the stack
            try:
                best_m = self.best_matches_on_l(cid, 10)
            except KeyError:
                best_m = ([], []) 
            fcent = self.cdfrom[cid].centroid()
            adjusted_centroid = fcent + v
            for tocid, candidate in best_m:
                d = adjusted_centroid.dist(candidate.centroid())
                if d < d_max:
                    ml[cid] = tocid
        self.current_ml = ml

    def display_match(self, array=None):
        pprint.pprint(self.current_ml)

        if array is not None:
            for cidfrom, cidto in self.current_ml.iteritems():
                cell_from = self.cdfrom[cidfrom]
                cell_to = self.cdto[cidto]
                centroid_from = cell_from.centroid()
                centroid_to = cell_to.centroid()

                vfrom = centroid_from
                vdisp = centroid_to - centroid_from

                draw_single_vector(array, vfrom, vdisp)

        print "Total numbers of matches:", len(self.current_ml)

    def build_centroid_array(self):
        #for (cid, cell) in self.cdto:
        centroids = [cell.centroid().astuple() for cid, cell in self.cdto]
        xs, ys = zip(*centroids)
        xdim, ydim = max(xs) + 1, max(ys) + 1
        self.centroid_array = np.zeros([xdim, ydim], dtype=np.uint32)
        for (cid, cell) in self.cdto:
            self.centroid_array[cell.centroid().astuple()] = cid

    def find_centroid(self, p):
        s = celldata.Coords2D((9, -38))
        cs = self.find_centroids_in_region(p, s, 10)

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
        
        cs = [x for x in np.nditer(subarray) if x != 0]

        return cs
    
    def __init__(self, celldata_from, celldata_to):
        self.cdfrom = celldata_from
        self.cdto = celldata_to

        ld1 = self.cdfrom.get_lnumbers()
        ld2 = self.cdto.get_lnumbers()

        self.build_centroid_array()
        self.lmatrix = lnumbers.make_matrix(ld1, ld2, lnumbers.smart_contrib)

    def best_matches_on_l(self, cid, n):
        #print "matchdata.best_matches_on_l"
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
