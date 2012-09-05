#!/usr/bin/env python2.7

import os
import sys
import math
import timeit
import pprint
import itertools

#import scipy
#import scipy.misc
import pygame
import pygame.display
from pygame import surfarray

import lnumbers

class Coords2D():
    def __init__(self, (x, y)):
        self.x = int(x)
        self.y = int(y)

    def dist(self, other):
        return abs(self - other)

    def __abs__(self):
        return math.sqrt(self.x * self.x + self.y * self.y)

    def __cmp__(self, other):
        if self.x == other.x and self.y == other.y:
            return 0
        else:
            return 1

    def __repr__(self):
        return "<Coords2D>: %d, %d" % (self.x, self.y)

    def __sub__(self, other):
        return Coords2D((self.x - other.x, self.y - other.y))
    
    def __add__(self, other):
        return Coords2D((self.x + other.x, self.y + other.y))

    def __mul__(self, other):
        return Coords2D((self.x * other.x, self.y * other.y))

    def __div__(self, other):
        return Coords2D((self.x / other, self.y / other))

    def __iter__(self):
        return iter((self.x, self.y))

    def astuple(self):
        return self.x, self.y

class Cell:
    def __init__(self, points_list):
        self.pl = points_list
        self.lnumbers = None
        if len(self.pl):
            self.ctroid = self.calc_centroid()
    
    def __iter__(self):
        return iter(self.pl)

    def __len__(self):
        return len(self.pl)

    def append(self, value):
        self.pl.append(value)

    def centroid(self):
        return self.ctroid

    def update_centroid(self):
        self.ctroid = self.calc_centroid()

    def calc_centroid(self):
        xs, ys = zip(*self.pl)
        x, y = sum(xs) / len(self.pl), sum(ys) / len(self.pl)
        return Coords2D((x, y))

    def set_area(self):
        self.area = len(self.pl)

    def set_lnumbers(self, ln):
        self.lnumbers = ln

    def __add__(self, other):
        tpl = list(self.pl) + list(other.pl)
        return Cell(tpl)


class CellData:
    def __init__(self, filename, lfile=None):
        cd = cell_dict_from_file(filename)
        self.cd = cd

        if lfile is not None:
            self.read_l_numbers(lfile)

        for cid, cell in self:
            cell.ctroid = cell.calc_centroid()
            cell.set_area()

    def __len__(self):
        return len(self.cd)

    def keys(self):
        return self.cd.keys()

    def __iter__(self):
        return self.cd.iteritems()

    def __getitem__(self, value):
        return self.cd[value]

    def __delitem__(self, item):
        del(self.cd[item])

    def read_l_numbers(self, filename):
        ln = lnumbers.parse_l_file(filename)

        for cid in ln:
            self[cid].set_lnumbers(ln[cid])

    def get_lnumbers(self):
        ld = {}
        for (cid, cell) in self:
            if self[cid].lnumbers is not None:
                ld[cid] = self[cid].lnumbers

        return ld
            
        

def cell_dict_from_file(image_file):
    """Take a numpy array containing values that represent segmentation ID, and return a
    dictionary keyed by the ID containing a list of points in absolute coordinates which
    comprise that cell"""

    try:
        imgsurface = pygame.image.load(image_file)
    except pygame.error, e:
        print "Couldn't load %s" % filename
        print e
        sys.exit(2)

    xdim, ydim = imgsurface.get_size()
    imgarray = surfarray.array2d(imgsurface)
    rs, gs, bs, ra = imgsurface.get_shifts()
    # TODO - work out what the hell is going on here (i.e. why does conversion
    # with the values returned above not work properly on some system
    rs, gs, bs = 16, 8, 0

    cmap = {}
    cd = {}
    for x in range(0, xdim):
        for y in range(0, ydim):

            val = imgarray[x, y]
            if val in cmap:
                c = cmap[val]
            else:
                r, g, b, a = imgsurface.unmap_rgb(val)
                c = (r << rs) + (g << gs) + (b << bs)
                cmap[val] = c

            if c not in cd: cd[c] = Cell([(x, y)])
            #if c not in cd: cd[c] = [(x, y)]
            else: cd[c].append((x, y))

    del cd[0]

    return cd

def some_testing(image_file, l_file):
    sx = 1
    sy = 1
    cd = cell_dict_from_file(image_file, sx, sy)

    with open(l_file, "r") as f:
        ls = [int(a.split(':')[0]) for a in f.readlines()]    

    a = set(ls)
    b = set(cd.keys())

def main():
    try:
        #image_file1 = sys.argv[1]
        #l_file = sys.argv[2]
        expname = sys.argv[1]
        tp = sys.argv[2]
    except IndexError:
        print "Usage: %s experiment time_point" % os.path.basename(sys.argv[0])
        sys.exit(0)

    sys.path.insert(0, '/Users/hartleym/local/python')
    import get_data_files as gdf

    d = gdf.get_data_files(expname, int(tp))

    ifile = d['Segmented image']
    lfile = d['L numbers']

    print ifile, lfile

    celldata = CellData(ifile, lfile)

    for (cid, cell) in celldata:
        print cid, cell.centroid()


if __name__ == '__main__':
    main()
