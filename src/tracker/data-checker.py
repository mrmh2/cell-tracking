#!/usr/bin/env python

import re
import os
import sys
from pprint import pprint

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
    #FIXME - pick out those we have sufficient data for rather than hack it
    dlist = [d[k] for k in sorted_nicely(d.keys()) if '-' not in k]
    # This is now something of a list incomprehension
    return [[a[n] for n in names if n in a] for a in dlist]

def main():
    try:
        expname = sys.argv[1]
        tp = int(sys.argv[2])
    except IndexError:
        print "Usage: %s experiment time_point" % os.path.basename(sys.argv[0])
        sys.exit(0)

    #names = ['Segmented image', 'L numbers', 'Projection', 'Microscope metadata']
    names = ['Segmented image', 'L numbers', 'Template segmented', 'Microscope metadata']
    #names = ['New segmented image', 'L numbers', 'Gaussian projection']
    expdata = load_data(expname, names)
    pprint(expdata)
    print expdata[tp]
    print expdata[tp + 1]
    ifile1, lfile1, pfile1, vfile1 = expdata[tp]
    ifile2, lfile2, pfile2, vfile2 = expdata[tp + 1]

    sys.exit(0)

if __name__ == '__main__':
    main()
