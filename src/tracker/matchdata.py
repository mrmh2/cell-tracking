#!/usr/bin/env python2.7

import os
import sys
import pprint
import random
from operator import itemgetter

import numpy as np

import celldata
from celldata import Coords2D
import lnumbers
from mutil import mean, msum, mkdir_p

def shades_of_jop():
    c1 = random.randint(127, 255) 
    c2 = random.randint(0, 127) 
    c3 = random.randint(0, 255) 

    #l = [c1, c2, c3]

    return tuple(random.sample([c1, c2, c3], 3))

class MatchData():
    def __init__(self, celldata_from, celldata_to):
        self.cdfrom = celldata_from
        self.cdto = celldata_to

        ld1 = self.cdfrom.get_lnumbers()
        ld2 = self.cdto.get_lnumbers()

        self.build_centroid_array()
        #self.lmatrix = lnumbers.make_matrix(ld1, ld2, lnumbers.weight_contrib)
        self.lmatrix = lnumbers.LMatrix(ld1, ld2) 

        self.hasdarray = False

        self.lm = 0.8
        self.um = 1.3

        for cid, cell in celldata_from:
            cell.color = shades_of_jop()

        self.current_ml = {}
        #self.current_ml = self.get_possible_ml()

    def single_iso_sample(self, ml):

        sd = {k : ml[k] for k in random.sample(ml, 15)}

        cs = []
        for fid, tids in sd.iteritems():
            fc = self.cdfrom[fid].centroid
            tc = self.cdto[tids[0]].centroid

            cs.append((fc, tc))


        return self.calc_iso_params(cs), sd


    def sampled_iso_params(self):
        ml = self.get_possible_ml()

        samples = [self.single_iso_sample(ml) for i in range(0, 50)]

        for ((c, v, s), ml) in samples:
            if s > 4:
                self.center, self.vd, self.s = c, v, s
                self.current_ml = ml

    def get_loby_candidates(self):
        lm = self.lmatrix
        lobiness = [(id, sum(vals[6:11])) for id, vals in lm.ln1.iteritems()]
        slobi = sorted(lobiness, key=itemgetter(1))
        blobi = slobi[-45:-5]

        return zip(*blobi)[0]

    def save_matchlist(self, filename):
        dirname = os.path.dirname(filename)
        if not os.path.exists(dirname):
            mkdir_p(dirname)
        with open(filename, 'w') as f:
            for k, v in self.current_ml.iteritems():
                f.write("%d: %s\n" % (k, v))

    def set_displacement(self, v):
        self.displacement = v

    def get_average_v(self):
        displacements = [ts[0].centroid - f.centroid for f, ts in self.itermatches()]
        if len(displacements):
            return sum(displacements, Coords2D((0, 0))) / len(displacements)
        else:
            return Coords2D((0, 0))
            
    def match_on_restricted_l(self, d_max, v):
        ml = {}
        #cids = self.cdfrom
        for cid, cell in self.cdfrom:
            # TODO - error handling should be further down the stack
            try:
                best_m = self.best_matches_on_l(cid, 15)
            except KeyError:
                best_m = ([], []) 
            fcent = self.cdfrom[cid].centroid
            adjusted_centroid = fcent + v
            for tocid, candidate in best_m:
                d = adjusted_centroid.dist(candidate.centroid)
                if d < d_max:
                    ml[cid] = [tocid]
        self.current_ml = ml

        self.update_displacement_array()

    def itermatches(self):
        for cidfrom, cidsto in self.current_ml.iteritems():
            cellsto = [self.cdto[cidto] for cidto in cidsto]
            yield self.cdfrom[cidfrom], cellsto

    def update_displacement_array(self):
        print "Centroid array", self.centroid_array.shape
        xdim, ydim = self.centroid_array.shape
        self.displacement_array = np.empty([xdim, ydim], dtype=np.object)
        #centroids = [(f.centroid
        # TODO - better, but now a bit long
        posdisp = [(f.centroid, sum(ts, celldata.Cell([])).centroid - f.centroid) 
                    for f, ts in self.itermatches()]
        #for fcell, tcells in self.itermatches():

        for vpos, vdisp in posdisp:
            x, y = vpos
            try:
                self.displacement_array[x, y] = vdisp - self.iso_vdisp(vpos)
            except IndexError:
                pass
        self.hasdarray = True

    def iterunmatched(self):
        i = ((cid, cell) for cid, cell in self.cdfrom if cid not in self.current_ml)

        return i

    def check_divide(self, cid):
    
        ll = self.lm
        ul = self.um
    
        to_cids = []
        #xd, yd = self.get_average_v()
        fcent = self.cdfrom[cid].centroid
        xd, yd = self.iso_vdisp(fcent) + self.get_displacement_a(fcent)
        print "Testing for divide in %d" % cid
        for x, y in self.cdfrom[cid]:
            #fcent = fromcell.centroid
            #v = self.iso_vdisp(fcent) + self.get_displacement_a(fcent)
            #xd, yd = self.iso_vdisp(((x, y)) + self.get_displacement_a((x, y)))
            #xd, yd = self.get_displacement_a((x, y))
            try:  
                c = self.centroid_array[x + xd, y + yd]
                if c != 0:
                    print "Found a centroid - %d" % c
                    to_cids.append(c)
            except IndexError:
                pass
    
        # TODO - consider all sets of 2
        if len(to_cids) > 1:
            #print "Testing potential divide: %d > %d, %d" % (cid, to_cids[0], to_cids[1])
            print "Testing divide: %d ->" % cid, to_cids
            fa = self.cdfrom[cid].area
            ta = sum([self.cdto[tocid].area for tocid in to_cids])
            #ta = self.cdto[to_cids[0]].area + self.cdto[to_cids[1]].area
            r = float(ta) / float(fa)
            print "Area ratio is %f" % r
            if r > ll and r < ul:
                #print "I think %d -> %d, %d" % (cid, to_cids[0], to_cids[1])
                return to_cids

        return []


    def get_known_divisions(self):
        for cellfrom, cellsto in self.itermatches():
            if len(cellsto) > 1:
                print 'divide'
    
    def get_divided_cells(self):
        ml = {}
        for cid, cell in self.iterunmatched():
            d = self.check_divide(cid)
            if len(d):
                ml[cid] = d

        self.divisions = ml
        self.current_ml.update(ml)
        #self.update_displacement_array()

    def get_displacement_a(self, p):

        if not self.hasdarray:
            return self.displacement
        x, y = p

        sr = 100

        search_array = self.displacement_array[x-sr:x+sr, y-sr:y+sr]

        values = search_array[np.nonzero(search_array)]
        if len(values):
            return sum(values, Coords2D((0, 0))) / len(values)
        else:
            return Coords2D((0, 0))

    def get_displacement_i(self, p):
        vd = p - Coords2D((352, 436))
    

    def match_with_displacement_field(self, d):
        ml = {}

        lm = self.lm
        um = self.um

        zero = Coords2D((0, 0))

        for cid, fromcell in self.cdfrom:
            fcent = fromcell.centroid
            #print "Attempting match for %d, at (%d, %d)" % (cid, fcent.x, fcent.y)
            v = self.get_displacement_a(fcent)
            if v != zero:
            #print "Local displacement is", v
                cs = self.find_centroid(fromcell.centroid, v, d)
                if cs != -1:
                    candidate = self.cdto[cs]
                    print "Areas:", fromcell.area, candidate.area
                    if candidate.area > lm * fromcell.area and candidate.area < um * fromcell.area:
                        ml[cid] = [cs]
    
        self.current_ml = ml
        self.update_displacement_array()

    def match_with_iso(self, d):
        ml = {}

        lm = self.lm
        um = self.um

        self.update_iso_params()

        zero = Coords2D((0, 0))

        for cid, fromcell in self.cdfrom:
            fcent = fromcell.centroid
            v = self.iso_vdisp(fcent)
            #print "Local displacement is", v
            cs = self.find_centroid(fromcell.centroid, v, d)
            if cs != -1:
                candidate = self.cdto[cs]
                print "Areas:", fromcell.area, candidate.area
                if candidate.area > lm * fromcell.area and candidate.area < um * fromcell.area:
                    ml[cid] = [cs]
    
        self.current_ml = ml
        self.update_displacement_array()

    def match_with_smarty_iso(self, d):
        ml = {}

        lm = self.lm
        um = self.um

        self.update_iso_params()
        self.update_displacement_array()
        zero = Coords2D((0, 0))

        for cid, fromcell in self.cdfrom:
            fcent = fromcell.centroid
            v = self.iso_vdisp(fcent) + self.get_displacement_a(fcent)
            #print "Local displacement is", v
            cs = self.find_centroid(fromcell.centroid, v, d)
            if cs != -1:
                candidate = self.cdto[cs]
                print "Areas:", fromcell.area, candidate.area
                if candidate.area > lm * fromcell.area and candidate.area < um * fromcell.area:
                    ml[cid] = [cs]
    
        self.current_ml = ml
        self.update_displacement_array()

    def stage_1_hinted_match(self, d):
        self.displacement = self.get_average_v()
        self.match_with_displacement_field(d)

    def stage_3_hinted_match(self, d):

        da = self.get_average_delta_a()

        self.lm = 0.8 * da
        self.um = 1.2 * da

        #self.match_with_displacement_field(d)
        self.match_with_smarty_iso(10)

    def stage_4_hinted_match(self, d):

        da = self.get_average_delta_a()

        self.lm = 0.8 * da

        self.get_divided_cells()


    def iso_vdisp(self, p):
        x, y = p
        #center = Coords2D((381, 499))
        #center = Coords2D((286, 408))
        # 2-3?
        #vd = Coords2D((30, 74))
        #vd = Coords2D((56, 55))
        #return ((p - center) / 7) + vd

        # 3 -> 4
        center = self.center#Coords2D((326, 516))
        vd = self.vd  #Coords2D((63, 80))
        return ((p - center) / self.s) + vd

        #return ((p - center) / 9) + vd

    def stage_2_hinted_match(self, d):
        #self.stage_2_hinted_match(d)
        #self.get_divided_cells()
        da = self.get_average_delta_a()

        self.lm = 0.8 * da
        self.um = 1.2 * da

        self.match_with_iso(10)

    def build_centroid_array(self):
        centroids = [cell.centroid.astuple() for cid, cell in self.cdto]
        xs, ys = zip(*centroids)
        xdim, ydim = max(xs) + 1, max(ys) + 1
        self.centroid_array = np.zeros([xdim, ydim], dtype=np.uint32)
        for (cid, cell) in self.cdto:
            self.centroid_array[cell.centroid.astuple()] = cid

    def find_centroid(self, p, v, d, debug=False):
        cs = self.find_centroids_in_region(p, v, d, debug)

        try:
            return cs[0]
        except IndexError:
            return -1

    def find_centroids_in_region(self, p, s, sr, debug=False):
        #s = p + celldata.Coords2D((9, -38))
        print "Looking at:", p, s
        sx, sy = p + s
        print "Slice around", sx, sy
        subarray = self.centroid_array[sx-sr:sx+sr, sy-sr:sy+sr]

        if debug: print subarray
        
        try:
            cs = [int(x) for x in np.nditer(subarray) if x != 0]
        except ValueError:
            return []

        return cs

    def get_possible_ml(self):
        pml = {id : self.lmatrix.best_n_matches(id, 5) 
                for id in self.get_loby_candidates()}
    
        for fid, tids in pml.iteritems():
            for tid in tids:
                delta_a = float(self.cdto[tid].area) / self.cdfrom[fid].area
                if delta_a < 1.0 or delta_a > 1.7:
                    pml[fid].remove(tid)
    
        ds = []
        for fid, tids in pml.iteritems():
            for tid in tids:
                ds.append(abs(self.cdto[tid].centroid - self.cdfrom[fid].centroid))
    
        med_d = sorted(ds)[len(ds)/3]
    
        for fid, tids in pml.iteritems():
            for tid in tids:
                d = abs(self.cdto[tid].centroid - self.cdfrom[fid].centroid)
                if d > med_d:
                    pml[fid].remove(tid)

        ml = {fid : pml[fid][:1] for fid in pml}

        return ml
    
    def best_matches_on_l(self, cid, n):
        cids = lnumbers.best_matches(self.lmatrix[cid], n)
        candidates = [self.cdto[c] for c in cids]
        return zip(cids, candidates)

    def get_average_delta_a(self):
        areas = [area_ratio(cellfrom, cellsto) 
                for cellfrom, cellsto 
                in self.itermatches()]

        return sum(areas) / len(areas)

    def calc_iso_params(self, cs):
        vdisps = [t - f for f, t in cs]
        vd = sum(vdisps, Coords2D((0, 0))) / len(vdisps)
        adj = [abs(v - vd) for v in vdisps]
        m = min(adj)
        #index of max element
        index = [i for i, j in enumerate(adj) if j == m][0]
        center = cs[index][0]
    
        top = [f - center for f, t in cs]
        bottom = [t - f - vd for f, t in cs]
    
        xp = zip([x for x, y in top], [x for x, y in bottom])
        xp = xp + zip([y for x, y in top], [y for x, y in bottom])
    
        s = mean([float(a)/float(b) for a, b in xp if b is not 0])

        return center, vd, s

    def update_iso_params(self):
        inp = [(f.centroid, msum([t for t in ts]).centroid )
        #inp = [(f.centroid, msum([t.centroid for t in ts]) )
            for f, ts in self.itermatches()]

        self.center, self.vd, self.s = self.calc_iso_params(inp)

    def print_match_stats(self):
        #print self.get_average_v()
        print self.get_average_delta_a()

        for cellfrom, cellsto in self.itermatches():
            print cellfrom.centroid, cellsto[0].centroid

        inp = [(f.centroid, msum([t for t in ts]).centroid )
            #centroid_to = sum([cellto for cellto in cellsto], celldata.Cell([])).centroid
            for f, ts in self.itermatches()]

        print self.calc_iso_params(inp)

def area_ratio(cellfrom, cellsto):
    return float(sum(cellto.area for cellto in cellsto)) / float(cellfrom.area)

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
