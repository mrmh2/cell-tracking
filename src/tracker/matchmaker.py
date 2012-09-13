#!/usr/bin/env python2.7

import re
import os
import sys
import pprint

import celldata
from celldata import Coords2D
import matchdisplay
import matchdata
import matchinteractor
from mltools import read_ml

def sorted_nicely( l ):
    """ Sort the given iterable in the way that humans expect."""
    convert = lambda text: int(text) if text.isdigit() else text
    alphanum_key = lambda key: [ convert(c) for c in re.split('([0-9]+)', key) ]
    return sorted(l, key = alphanum_key)

def load_data(expname, names):
    sys.path.insert(0, os.path.join(os.environ['HOME'], 'local/python'))
    import get_data_files as gdf
    d = gdf.get_data_files(expname)

    dlist = [d[k] for k in sorted_nicely(d.keys())]
    # This is now something of a list incomprehension
    return [[a[n] for n in names if n in a] for a in dlist]

def matchdata_from_exp_and_tp(expname, tp, names):
    #names = ['Segmented image', 'L numbers', 'Projection']
    #names = ['New segmented image', 'L numbers', 'Gaussian projection']
    expdata = load_data(expname, names)
    ifile1, lfile1, pfile1 = expdata[tp]
    ifile2, lfile2, pfile2 = expdata[tp + 1]
  
    celldata1 = celldata.CellData(ifile1)
    celldata2 = celldata.CellData(ifile2)

    #celldata1 = celldata.CellData(ifile1, lfile1)
    #celldata2 = celldata.CellData(ifile2, lfile2)
    # until we fix the l number generation
    try:
        del(celldata1[1])
        del(celldata2[1])
    except KeyError:
        pass
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
    #names = ['New segmented image', 'L numbers', 'Gaussian projection']
    expdata = load_data(expname, names)
    ifile1, lfile1, pfile1 = expdata[tp]
    ifile2, lfile2, pfile2 = expdata[tp + 1]
 
    mda = matchdata_from_exp_and_tp(expname, tp, names)
    mdisplay = matchdisplay.MatchDisplay(ifile1, ifile2, pfile1, pfile2, mda)
    mint = matchinteractor.MatchInteractor(mdisplay)

    ml = read_ml('T01T02.match')
    mda.current_ml = ml
    v = mda.get_average_v()
    mdisplay.display_match(v)

    mint.run()

if __name__ == '__main__':
    main()
