#!/usr/bin/env python

def get_list(rawlist):
    tl = rawlist.translate(None, ' []')
    ids = [int(i) for i in tl.split(',')]
    return ids

def read_ml(filename):
    with open(filename, 'r') as f:
        lines = [l.strip() for l in f.readlines()]

    splitlines = (l.split(':') for l in lines)

    return dict([(int(cfrom), get_list(cto)) for cfrom, cto in splitlines])
