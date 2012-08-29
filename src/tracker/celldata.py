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

def compositeRGB_to_components(c):
    R = c % 256
    G = int(c / 256) % 256
    B = int(c / (256 * 256)) % 256

    return (R, G, B)

def mangle_colour_value(c):
    r, g, b = compositeRGB_to_components(c)
    return b + 256 * g + 256 * 256 * r

def build_celldict(imgarray):
    """Take a numpy array containing values that represent segmentation ID, and return a
    dictionary keyed by the ID containing a list of points in absolute coordinates which
    comprise that cell"""
    # TODO - probably (definitely) smarter ways to do this

    xdim, ydim = imgarray.shape
    cd = {}
    # Color values are mangled for some reason. Rather than recalculate the mangled color 
    # value for every single pixel in the image, let's build a hash table (dictionary)
    # as we go along
    md = {}
    
    for x in range(0, xdim):
        for y in range (0, ydim):
            c = imgarray[x, y]

            if md.has_key(c):
                a = md[c]
            else:
                md[c] = mangle_colour_value(c)
                a = md[c]

            if not cd.has_key(a): cd[a] = [(x, y)]
            else: cd[a].append((x, y))

    return cd

def cell_dict_from_file(image_file, sx, sy):  
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
    imgsurface = pygame.transform.scale(imgsurface, (int(xdim * sx), int(ydim * sy)))
    xdim, ydim = imgsurface.get_size()
    imgarray = surfarray.array2d(imgsurface)

    cmap = {}
    cd = {}
    for x in range(0, xdim):
        for y in range(0, ydim):

            val = imgarray[x, y]
            if val in cmap:
                c = cmap[val]
            else:
                r, g, b, a = imgsurface.unmap_rgb(val)
                c = b + 256 * g + 256 * 256 * r
                cmap[val] = c

            if c not in cd: cd[c] = Cell([(x, y)])
            #if c not in cd: cd[c] = [(x, y)]
            else: cd[c].append((x, y))

    return cd

def old_cell_dict_from_file(filename, sx, sy):
    try:
        imgsurface = pygame.image.load(filename)
        xdim, ydim = imgsurface.get_size()
        imgsurface = pygame.transform.scale(imgsurface, (int(xdim * sx), int(ydim * sy)))
        imgarray = surfarray.array2d(imgsurface)
        cd = build_celldict(imgarray)
    except pygame.error, e:
        print "Couldn't load %s" % filename
        print e
        sys.exit(2)

    return cd

class CellData:
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

    #print sorted(list(a  - (a & b)))
    #print sorted(list(b  - (a & b)))


def main():
    try:
        image_file = sys.argv[1]
    except IndexError:
        print "Usage: %s image_file" % os.path.basename(sys.argv[0])
        sys.exit(0)

    cd = cell_dict_from_file(image_file, 1, 1)

    #for p in cd[12]:
    #    print p
   
if __name__ == '__main__':
    main()
