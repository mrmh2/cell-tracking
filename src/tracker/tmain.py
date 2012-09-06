#!/usr/bin/env python2.7

import re
import os
import sys
import pprint

import celldata
from celldata import Coords2D
import matchdisplay
import matchdata

class MatchAlgorithm(object):
    # Generate inital guess at displacement vector somehow - use l numbers for guidance

    def __init__(self, mda, tp, mdisplay=None):
        self.mda = mda
        if mdisplay is not None:
            self.mdisplay = mdisplay

        self.tp = tp

    def run(self):
        mda = self.mda
        mdisplay = self.mdisplay
        if self.tp == 5:
            v = celldata.Coords2D((4, -38))
            mda.set_displacement(v)
            mda.match_on_restricted_l(7, v)
            mdisplay.display_match(v)
        elif self.tp == 6:
            v = celldata.Coords2D((4, -13))
            mda.set_displacement(v)
        #v = celldata.Coords2D((1, 1))
        # 6 -> 7
        # 7 -> 8
        #v = celldata.Coords2D((71, 42))
        #mda.current_ml = start_ml
        #mda.update_displacement_array()
        #mda.display_match(ov1, ov2, npa)
    
        mda.lm = 0.95
        mda.um = 1.2
        mda.match_with_displacement_field(5)
        mdisplay.display_match(v)
        mda.lm = 0.90
        mda.um = 1.25
        mda.match_with_displacement_field(6)
        mdisplay.display_match(v)
        mda.lm = 0.85
        mda.um = 1.3
        mda.match_with_displacement_field(7)
        mdisplay.display_match(v)
        mda.lm = 0.78
        mda.um = 1.35
        mda.match_with_displacement_field(8)
        mdisplay.display_match(v)
        mda.match_with_displacement_field(9)
        mdisplay.display_match(v)
    
        mda.get_divided_cells()
        mdisplay.display_match(v)

def sorted_nicely( l ):
    """ Sort the given iterable in the way that humans expect."""
    convert = lambda text: int(text) if text.isdigit() else text
    alphanum_key = lambda key: [ convert(c) for c in re.split('([0-9]+)', key) ]
    return sorted(l, key = alphanum_key)

def load_data(expname, names):
    sys.path.insert(0, os.path.join(os.environ['HOME'], 'local/python'))
    import get_data_files as gdf
    d = gdf.get_data_files(expname)
    pprint.pprint(d)

    dlist = [d[k] for k in sorted_nicely(d.keys())]
    return [[a[n] for n in names] for a in dlist]

def matchdata_from_exp_and_tp(expname, tp):
    names = ['Segmented image', 'L numbers', 'Projection']
    expdata = load_data(expname, names)
    ifile1, lfile1, pfile1 = expdata[tp]
    ifile2, lfile2, pfile2 = expdata[tp + 1]
  
    celldata1 = celldata.CellData(ifile1, lfile1)
    # until we fix the l number generation
    del(celldata1[1])
    celldata2 = celldata.CellData(ifile2, lfile2)
    del(celldata2[1])
    mda = matchdata.MatchData(celldata1, celldata2)

    return mda
 
def main():
    try:
        expname = sys.argv[1]
        tp = int(sys.argv[2])
    except IndexError:
        print "Usage: %s experiment time_point" % os.path.basename(sys.argv[0])
        sys.exit(0)

    names = ['Segmented image', 'L numbers', 'Projection']
    expdata = load_data(expname, names)
    ifile1, lfile1, pfile1 = expdata[tp]
    ifile2, lfile2, pfile2 = expdata[tp + 1]
 
    mda = matchdata_from_exp_and_tp(expname, tp)
    mdisplay = matchdisplay.MatchDisplay(ifile1, ifile2, pfile1, pfile2, mda)
    mdisplay.update()

    mymatch = MatchAlgorithm(mda, tp, mdisplay)
    mymatch.run()

     #start_ml = {
    #            432: 698,
    #            686: 1120,
    #            585: 974,
    #            739: 1186,
    #            548: 924,
    #            537: 913}

    #5 -> 6
    mdisplay.run()

if __name__ == '__main__':
    main()
