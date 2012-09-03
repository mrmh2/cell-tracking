#!/usr/bin/env python2.7

import os
import sys

import numpy as np
import pygame
import pygame.surfarray as surfarray
from pygame.locals import *

import bb
import display
import intarray
import celldata
import displaymanager as dm
import matchdisplay
import matchdata
import lnumbers

class MatchAlgorithm():
    pass
    # Generate inital guess at displacement vector somehow - use l numbers for guidance

class CompTracker():
    def __init__(self, ov1, ov2, cd1, cd2, mda, midov):
        self.ov1 = ov1
        self.ov2 = ov2
        self.cd1 = cd1
        self.cd2 = cd2
        self.mda = mda
        self.midov = midov

        self.leftcell = None
        self.rightcell = None

    def set_left(self, cid):
        self.leftcell = self.cd1[cid]
        self.ov1.plot_points(self.cd1[cid], (255, 255, 255))
        print self.midov.array.shape
        self.midov.plot_points(self.cd1[cid], (255, 255, 255))
        print "Set left to %d" % cid
        print self.leftcell.lnumbers
        best_m = self.mda.best_matches_on_l(cid, 10)

#        self.ov2.blank()
#        for i in range(0, 10):
#            col = 255 - i * 20, 0, 0
#            self.ov2.plot_points(best_m[i], col)
#        candidate = best_m[0]
#        self.midov.plot_points(candidate, (255, 0, 0))
#        self.comp()
#
        fcent = self.mda.cdfrom[cid].centroid()
        adjusted_centroid = fcent + celldata.Coords2D((9, -38))
        print "From ", adjusted_centroid
        for cid, candidate in best_m:
            #candidate = self.mda.cdto[match_cid]
            d = adjusted_centroid.dist(candidate.centroid())
            if d < 10:
                self.ov2.plot_points(candidate, (255, 255, 255))

    def set_right(self, cid):
        self.rightcell = self.cd2[cid]
        self.ov2.plot_points(self.cd2[cid], (255, 255, 255))
        print "Set right to %d" % cid
        print self.rightcell.lnumbers
        self.comp()

    def comp(self):
        if self.leftcell and self.rightcell:
            print lnumbers.weighted_l_distance(self.leftcell.lnumbers, self.rightcell.lnumbers, lnumbers.smart_contrib)

def overlay_highlighter(ov, cd):

    def highlight_it(cid):
        ov.plot_points(cd[cid], (255, 255, 255))
        print cd[cid].lnumbers

    return highlight_it

def make_matcher(md, ov):

    def print_it(cid):
        best = md.best_matches_on_l(cid, 1)[0]
        ov.plot_points(md.cdto[cid], (255, 255, 255))

    return print_it

def testfunc(cid):
    print "Sproink!", cid

def input_loop(events, scale, dmanager):

    px, py = 0, 0

    for event in events:
        if event.type == QUIT:
            sys.exit(0)
        elif event.type == KEYDOWN:
            print event.key
            if event.key == 45:
                scale = 0.9 * scale
            if event.key == 61:
                scale = scale / 0.9
            if event.key == 275:
                px = -100
            if event.key == 276:
                px = 100
            if event.key == 273:
                py = 100
            if event.key == 274:
                py = -100
            if event.key == 314:
                dmanager.key_input(314)
        elif event.type == MOUSEBUTTONDOWN:
            x, y = pygame.mouse.get_pos()
            dmanager.mouse_input((x, y), event.button)

    pan = (px, py)

    return scale, pan

def main():

    xdim = 1024
    ydim = 600
    caption_string = "Display test"
    sf = 'Segmented image'
    of = 'Projection'
    #sf = 'Rotated image'
    #of = 'Rotated projection'

    try:
        expname = sys.argv[1]
        tp = sys.argv[2]
    except IndexError:
        print "Usage: %s experiment time_point" % os.path.basename(sys.argv[0])
        sys.exit(0)
   
    sys.path.insert(0, '/Users/hartleym/local/python')
    import get_data_files as gdf
    d1 = gdf.get_data_files(expname, int(tp))
    d2 = gdf.get_data_files(expname, int(tp) + 1)
    image_file = d1[sf]
    l_file = d1['L numbers']
    proj_file = d1[of]
    image_file2 = d2[sf]
    l_file2 = d2['L numbers']
    proj_file2 = d2[of]

    #imgsurface = pygame.image.load(image_file)
    td = display.TrackerDisplay(xdim, ydim, caption_string)

    xdim, ydim = td.get_size()

    scale = 0.5
    px, py = 0, 0

    dmanager = dm.DisplayManager(td)

    bbox = bb.BoundingBox((0, 0), (xdim/3, ydim))
    bbox2 = bb.BoundingBox((2 * xdim/3, 0), (xdim/3, ydim))
    bbox3 = bb.BoundingBox((xdim/3, 0), (xdim/3, ydim))

    da = dm.DisplayArea(bbox)
    de = dm.ImageElement(image_file)
    xdim1, ydim1 = de.xdim, de.ydim
    ia1 = intarray.InteractorArray(de.imgarray) 
    de.iarray = ia1
    de2 = dm.ImageElement(proj_file, array=False)
    de2.visible = False
    da.add_element(de)
    da.add_element(de2)
    ov1 = de.generate_overlay()
    da.add_element(ov1)
    dmanager.add_area(da)

    da = dm.DisplayArea(bbox2)
    de = dm.ImageElement(image_file2)
    xdim2, ydim2 = de.xdim, de.ydim
    de2 = dm.ImageElement(proj_file2, array=False)
    de2.visible = False
    ia2 = intarray.InteractorArray(de.imgarray) 
    de.iarray = ia2
    da.add_element(de)
    da.add_element(de2)
    ov2 = de.generate_overlay()
    da.add_element(ov2)
    dmanager.add_area(da)

    npaxdim = max(xdim1, xdim2)
    npaydim = max(ydim1, ydim2)

    da = dm.DisplayArea(bbox3)
    npa = np.zeros([npaxdim, npaydim, 3], dtype=np.int8)
    midov = dm.OverlayElement(npa)
    da.add_element(midov)
    dmanager.add_area(da)

    dmanager.update()

    celldata1 = celldata.CellData(image_file, l_file)
    # until we fix the l number generation
    del(celldata1[1])
    celldata2 = celldata.CellData(image_file2, l_file2)
    mda = matchdata.MatchData(celldata1, celldata2)
    #ia1.onclick = overlay_highlighter(ov1, celldata1)

    #ia1.onclick = make_matcher(mda, ov2)

    #myhigh = overlay_highlighter(ov2, celldata2)

    #myhigh(568)

    #ov1.plot_points(celldata1[15], (255, 255, 255))

    ct = CompTracker(ov1, ov2, celldata1, celldata2, mda, midov)
    ia1.onclick = ct.set_left
    ia2.onclick = ct.set_right

    v = celldata.Coords2D((9, -38))
    mda.match_on_restricted_l(10, v)
    mda.display_match(npa)

    #for x in range(50, 100):
    #    for y in range(50, 100):
    #        npa[x, y] = 0, 0, 255

    while True:
        scale, (pan_x, pan_y) = input_loop(pygame.event.get(), scale, dmanager)
        px += pan_x
        py += pan_y
        dmanager.update()
        #dm.draw(screen)

if __name__ == '__main__':
    main()
