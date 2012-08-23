#!/usr/bin/env python

import pprint
import sys
import os
import subprocess
import random
import shutil

orgpath = "data2/original/"
segpath = "data2/segmented/"
lpath = "data2/lnumbers/"
lcommand = "bin/getLnumbers"
parfile = "data/matchyourcell_01.par"
genlfile = "lcoeffs.txt"
outfile = "trackdata2.txt"

def make_l_directory():
    try:
        os.mkdir(lpath)
    except OSError, e:
        #TODO - some more error handling here...
        pass

def presep(filename):
    return filename.split(".")[0]

def get_datapoints(orgpath, segpath):
    orgfiles = os.listdir(orgpath)
    segfiles = os.listdir(segpath)

    datapoints = {}

    for of in orgfiles:
        print "Checking for segmented version of %s" % of
        for sf in segfiles:
            if sf.find(presep(of)) != -1:
                datapoints[os.path.join(orgpath, of)] = os.path.join(segpath, sf)

    return datapoints

def generate_l_coeffs(of, sf, lf):
    runcommand = [lcommand, parfile, "tmp", of, sf, sf]

    print "Generating %s" % lf
    p = subprocess.Popen(runcommand, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    #TODO - Error handling
    o, se = p.communicate()

    #print se, so

    #print "From %s to %s" % (genlfile, lf)
    shutil.copy(genlfile, lf)
 
def main():

    datapoints = get_datapoints(orgpath, segpath)

    pprint.pprint(datapoints)

    #for dp in datapoints:
    #    generate_l_coeffs(dp, datapoints[dp])

    make_l_directory()
    with open(outfile, "w") as f:
        for dp in sorted(datapoints.keys()):
            of = dp
            sf = datapoints[dp]
            lf = os.path.join(lpath, presep(os.path.basename(dp)) + ".lcoeff")
            if not os.path.isfile(lf): generate_l_coeffs(dp, datapoints[dp], lf)
            f.write("%s,%s,%s\n" % (of, sf, lf))


if __name__ == "__main__":
    main()
