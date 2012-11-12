#!/usr/bin/env python2.7

import re
import os
import sys
import errno
import pprint
import ConfigParser

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

def get_voxel_spacing(filename):

    config = ConfigParser.SafeConfigParser()
    config.read(filename)
    sname = 'Microscope data'
    
    vx = float(config.get(sname, 'voxel size x'))
    vy = float(config.get(sname, 'voxel size y'))
    vz = float(config.get(sname, 'voxel size z'))

    return vx, vy, vz

def matchdata_from_exp_and_tp(expname, tp, names):
    expdata = load_data(expname, names)
    ifile1, lfile1, pfile1, vfile1 = expdata[tp]
    ifile2, lfile2, pfile2, vfile2 = expdata[tp + 1]

    sx1, sy1, sz1 = get_voxel_spacing(vfile1)
    sx2, sy2, sz2 = get_voxel_spacing(vfile2)
  
    celldata1 = celldata.CellData(ifile1, lfile=lfile1)
    celldata2 = celldata.CellData(ifile2, lfile=lfile2, scale=(sx2/sy1, sy2/sy1))
    #celldata2 = celldata.CellData(ifile2)

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

    names = ['Segmented image', 'L numbers', 'Projection', 'Microscope metadata']
    #names = ['New segmented image', 'L numbers', 'Gaussian projection']
    expdata = load_data(expname, names)
    ifile1, lfile1, pfile1, vfile1 = expdata[tp]
    ifile2, lfile2, pfile2, vfile2 = expdata[tp + 1]

    sx1, sy1, sz1 = get_voxel_spacing(vfile1)
    sx2, sy2, sz2 = get_voxel_spacing(vfile2)

    mda = matchdata_from_exp_and_tp(expname, tp, names)

    mname = 'T%02dT%02d.match' % (tp, tp + 1)
    try:
        ml = read_ml(mname)
    except IOError, e:
        if e.errno == errno.ENOENT:
            ml = {}
        else: raise

    mda.current_ml = ml
    #mda.current_ml = mda.get_possible_ml()
    #mda.sampled_iso_params()

    mdisplay = matchdisplay.MatchDisplay(ifile1, ifile2, pfile1, pfile2, mda, 
        scale=(sx2/sx1, sy2/sy1))
    mint = matchinteractor.MatchInteractor(mdisplay)

    v = mda.get_average_v()
    mdisplay.display_match(v)

    mint.run()

if __name__ == '__main__':
    main()
