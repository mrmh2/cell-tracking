#!/usr/bin/env python

import sys
import pickle
import hashlib
import os

def parse_line(l):
    cellid, sep, lcraw = l.strip().partition(": ")
    return int(cellid), [float(f) for f in lcraw.split("  ")]

def parse_l_file(filename):

    try:
        with open(filename, "r") as f:
            lines = f.readlines()
    except IOError, e:
        print "Failed to load %s" % filename
        print e
        sys.exit(2)

    ld = {}

    for l in lines:
        cid, lcs = parse_line(l)
        ld[cid] = lcs

    return ld

def l_distance(lc1, lc2):
    #TODO numpyisation
    return sum([pow(a - b, 2) for (a, b) in zip(lc1, lc2)])

def comp_contrib(ln, la, lb):
    return pow(la - lb, 2)

def weight_contrib(ln, la, lb):
    return ln * pow(la - lb, 2)

def smart_contrib(ln, la, lb):
    if ln > 8: return 0
    return ln * pow(la - lb, 2)

def weighted_l_distance(lc1, lc2, comp_func):
    lzs = zip(range(0, 15), lc1, lc2)

    #return sum([comp_contrib(n, a, b) for (n, a, b) in lzs])
    return sum([comp_func(n, a, b) for (n, a, b) in lzs])
    #return sum([weight_contrib(n, a, b) for (n, a, b) in lzs])

def best_matches(d, n):
    b = d.keys()
    b.sort(key=d.__getitem__)

    return b[:n]

def best_matches_with_scores(d, n):
    b = d.keys()
    b.sort(key=d.__getitem__)

    bm = {}
    for i in b[:n]:
        bm[i] = d[i]

    return bm

def score_best_match(d):

    ##TODO - this is a horrible function, make it better
    bms = best_matches_with_scores(d, 2)

    ks = bms.keys()

    k0 = bms[ks[0]]
    k1 = bms[ks[1]]

    if k0 < k1:
        return ks[0], k1 - k0
    else:
        return ks[1], k0 - k1

def make_matrix(ld1, ld2, comp_func):
    m = {}
    for c1 in ld1.keys():
        d = {}
        for c2 in ld2.keys():
            #d[c2] = l_distance(ld1[c1], ld2[c2])
            #d[c2] = weighted_l_distance(ld1[c1], ld2[c2])
            d[c2] = weighted_l_distance(ld1[c1], ld2[c2], comp_func)
        m[c1] = d

    return m


def build_matrix_from_files(lfile1, lfile2, comp_func):

    ld1 = parse_l_file(lfile1)
    ld2 = parse_l_file(lfile2)

    return make_matrix(ld1, ld2, comp_func)

def save_matrix(m, filename):
    try:
        with open(filename, 'wb') as f:
            pickle.dump(m, f)
    except IOError, e:
        print "Failed to open %s for writing" % filename
        print e
        sys.exit(0)

def build_matrix(lfile1, lfile2, comp_func=comp_contrib, cachedir='/tmp/cache'):

    #print "Build matrix on %s, %s" % (lfile1, lfile2)

    #print hashlib.algorithms

    if cachedir == None:
        return build_matrix_from_files(lfile1, lfile2, comp_func)

    pickhash = hashlib.sha256(lfile1 + lfile2).hexdigest() + '.p'
    
    pickname = os.path.join(cachedir, pickhash)

    try:
        with open(pickname, 'rb') as f:
            print "Reading cached file...",
            m = pickle.load(f)
            print "done"
    except IOError, e:
        if str(e).find("No such file") != -1:
            m = build_matrix_from_files(lfile1, lfile2, comp_func)
            save_matrix(m, pickname)
        else:
            print "Reading cached file failed"
            print e
            sys.exit(0)

    return m

def debug_stuff(lfile1, lfile2, c1):
    ld1 = parse_l_file(lfile1)
    ld2 = parse_l_file(lfile2)

    m = make_matrix(ld1, ld1)

    print best_matches(m[c1], 5)

    #for c2 in ld2.keys():
    #    print l_distance(ld1[c1], ld2[c2]), ld2[c2]

    print ld1[c1]

def mysort(k):
    x, (y, z) = k
    return z

def most_distinctive(m, n):
    allscores = [(c, score_best_match(m[c])) for c in m.keys()]

    allscores.sort(key=mysort)
    allscores.reverse()

    cids = [x for (x, (y, z)) in allscores]

    return cids[:n]

def dump_matrix(m, filename):
    try:
        with open(filename, "wb") as f:
            pickle.dump(m, f)
    except IOError, e:
        print "ERROR: something with %s" % filename
        print e
        sys.exit(0)

def read_matrix(filename):
    try:
        with open(filename, "r") as f:
            m = pickle.load(f)
    except IOError, e:
        print "ERROR: something with %s" % filename
        print e
        sys.exit(0)

    return m

def main():
    lfile1 = "lnumbers/spch1_03_t07_cropped.lcoeff"
    lfile2 = "lnumbers/spch1_03_t10_cropped.lcoeff"

    m = build_matrix(lfile1, lfile2, comp_contrib)

    #dump_matrix(m, "test.dump")

    #m = read_matrix("test.dump")

    #debug_stuff(lfile1, lfile2, 21982)

    #print best_matches(m[21982], 5)
    ##print best_matches(m[17142], 5)
    #for c in m.keys():
    #    bm, score = score_best_match(m[k])
    #    print c, bm, score

    print most_distinctive(m, 5)

if __name__ == "__main__":
    main()
