#!/usr/bin/env python2.7

import os
import sys
import timeit
import pprint

#import scipy
#import scipy.misc
import pygame
import pygame.display
from pygame import surfarray

class Cell:
    def __init__(self, points_list):
        self.pl = points_list
    
    def __iter__(self):
        return iter(self.pl)

    def __len__(self):
        return len(self.pl)

    def append(self, value):
        self.pl.append(value)

class CellData:
    def __init__(self, filename):
        cd = cell_dict_from_file(filename)
        self.cd = cd

    def keys(self):
        return self.cd.keys()

    def __getitem__(self, value):
        return self.cd[value].pl

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

    return cd

class OldCellData:
    def __init__(self, filename, sx, sy, cachedir='/mnt/tmp'):
        self.cd = cell_dict_from_file(filename, sx, sy)

    def set_disp_panel(self, disp_panel):
        self.disp_panel = disp_panel

    def highlight_cell(self, cid, col, array=None):
        if array is None:
            try: 
                array = self.disp_panel.array
            except AttributeError:
                print "ERROR: No array to display to in highlight_cell"
                sys.exit(2)
        c = rgb_to_comp(col)
        for x, y in self.cd[cid]:
            array[x, y] = c

    def relative_rep(self, cid):
        ox, oy = get_centroid(self.cd[cid])

        npl = []
        for x, y in self.cd[cid]:
            npl.append((x - ox, y - oy))

        return npl

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
        image_file1 = sys.argv[1]
        image_file2 = sys.argv[2]
    except IndexError:
        print "Usage: %s image_file1 image_file2" % os.path.basename(sys.argv[0])
        sys.exit(0)

    celldata1 = CellData(image_file1)
    #celldata2 = CellData(image_file2)

    print celldata1.keys()
    #print celldata1[15]


if __name__ == '__main__':
    main()
