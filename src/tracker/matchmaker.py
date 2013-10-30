#!/usr/bin/env python2.7

import re
import os
import sys
import errno
from pprint import pprint
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
    #d = gdf.get_data_files(expname)
    d = gdf.get_files_dictionary(expname)
    #dlist = [d[k] for k in sorted_nicely(d.keys())]
    dlist = [d[k] for k in sorted_nicely(d.keys()) if '-' not in k]
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
    if 'L numbers' in names:
        ifile1, lfile1, pfile1, vfile1 = expdata[tp]
        ifile2, lfile2, pfile2, vfile2 = expdata[tp + 1]
    else:
        ifile1, pfile1, vfile1 = expdata[tp]
        ifile2, pfile2, vfile2 = expdata[tp + 1]
        lfile1 = None
        lfile2 = None

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

def available_data_stages(expname):
    sys.path.insert(0, os.path.join(os.environ['HOME'], 'local/python'))
    import get_data_files as gdf
    d = gdf.get_files_dictionary(expname)

    # Get the list of unique data stages
    # sum(l, []) turns list of lists into flat list
    return set(sum([s.keys() for s in d.values()], []))

def wir(expname, name):
    """Check whether at least one time point has the datum with name name.
    e.g. wir("ExpID3078/plantA", "template_segmented" returns true if the
    data set ExpID3078 has the templated_segmented category with at least
    one datum in it."""

    return name in available_data_stages(expname)
    
 
def main():
    try:
        expname = sys.argv[1]
        tp = int(sys.argv[2])
    except IndexError:
        print "Usage: %s experiment time_point" % os.path.basename(sys.argv[0])
        sys.exit(0)


    names = []
    if wir(expname, 'Segmented corrected'):
        names += ['Segmented corrected']
    elif wir(expname, 'Segmented image'):
        names += ['Segmented image']
    else:
        print "No segmented image"
        sys.exit(2)

    if wir(expname, 'L numbers'):
        names += ['L numbers']

    if wir(expname, 'Template segmented'):
        names += ['Template segmented']
    elif wir(expname, 'Gaussian projection'):
        names += ['Gaussian projection']
    else:
        print "No segmented image"
        sys.exit(2)

    names += ['Microscope metadata']

    #names = ['Segmented image', 'L numbers', 'Projection', 'Microscope metadata']
    #names = ['Segmented image', 'L numbers', 'Template segmented', 'Microscope metadata']
    #names = ['New segmented image', 'L numbers', 'Gaussian projection']
    expdata = load_data(expname, names)

    print names
    print expdata[tp]

    #pprint(expdata)
    #sys.exit(0)

    if 'L numbers' in names:
        ifile1, lfile1, pfile1, vfile1 = expdata[tp]
        ifile2, lfile2, pfile2, vfile2 = expdata[tp + 1]
    else:
        ifile1, pfile1, vfile1 = expdata[tp]
        ifile2, pfile2, vfile2 = expdata[tp + 1]

    sx1, sy1, sz1 = get_voxel_spacing(vfile1)
    sx2, sy2, sz2 = get_voxel_spacing(vfile2)

    mda = matchdata_from_exp_and_tp(expname, tp, names)

    mname = os.path.join(expname, 'matches', 'T%02dT%02d.match' % (tp, tp + 1))
    print 'Looking for match list: %s' % mname
    try:
        ml = read_ml(mname)
        print 'Read match list from file, %d matches' % len(ml)
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
    mint.filename = mname

    v = mda.get_average_v()
    mdisplay.display_match(v)

    mint.run()

if __name__ == '__main__':
    main()
