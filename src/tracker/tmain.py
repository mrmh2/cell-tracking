#!/usr/bin/env python2.7

import os
import sys
import pprint

import numpy as np
import pygame
import pygame.surfarray as surfarray
import scipy.misc
from pygame.locals import *

import bb
import display
import intarray
import celldata
from celldata import Coords2D
import displaymanager as dm
import matchdisplay
import matchdata
import lnumbers

def is_border(x, y, pl):
    xoffsets = [-1, 0, 1]
    yoffsets = [-1, 0, 1]

    for ox in xoffsets:
        for oy in yoffsets:
            if (x + ox, y + oy) not in pl:
                return True

    return False
        
def border_list(pl):

    print "Have to check %d points" % len(pl)
    return [(x, y) for (x, y) in pl if is_border(x, y, pl) == True]

def shiftit(pl, v):
    xd, yd = v

    return [(x + xd, y + yd) for (x, y) in pl]

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
        print "Set left to %d, area %d, centroid %s" % (cid, self.leftcell.area, self.leftcell.centroid)
        self.ov1.plot_points(self.cd1[cid], (255, 255, 255))
        v = Coords2D((4, -38))
        v = self.mda.get_displacement_a(self.leftcell.centroid)
        self.ov2.plot_points(shiftit(border_list(self.cd1[cid]), v), (255, 255, 255))
        print self.midov.array.shape
        self.midov.plot_points(self.cd1[cid], (255, 255, 255))
        print self.leftcell.lnumbers
        best_m = self.mda.best_matches_on_l(cid, 10)
        pprint.pprint(best_m)

#        self.ov2.blank()
#        for i in range(0, 10):
#            col = 255 - i * 20, 0, 0
#            self.ov2.plot_points(best_m[i], col)
#        candidate = best_m[0]
#        self.midov.plot_points(candidate, (255, 0, 0))
#        self.comp()
#
        fcent = self.mda.cdfrom[cid].centroid
        adjusted_centroid = fcent + celldata.Coords2D((9, -38))
        #print "From ", adjusted_centroid
        for cid, candidate in best_m:
            #candidate = self.mda.cdto[match_cid]
            d = adjusted_centroid.dist(candidate.centroid)
            if d < 10:
                self.ov2.plot_points(candidate, (255, 255, 255))

    def set_right(self, cid):
        self.rightcell = self.cd2[cid]
        self.ov2.plot_points(self.cd2[cid], (255, 255, 255))
        print "Set right to %d, area %d, centroid %s" % (cid, self.rightcell.area, self.rightcell.centroid)
        print self.rightcell.lnumbers
        self.comp()

    def comp(self):
        if self.leftcell and self.rightcell:
            pass
            #print lnumbers.weighted_l_distance(self.leftcell.lnumbers, self.rightcell.lnumbers, lnumbers.smart_contrib)

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
            if event.key == 314 or event.key == 96:
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
   
    localdir = os.path.join(os.getenv('HOME'), 'local/python')
    print localdir
    sys.path.insert(0, os.path.join(os.environ['HOME'], 'local/python'))
    import get_data_files as gdf
    d1 = gdf.get_data_files(expname, int(tp))
    d2 = gdf.get_data_files(expname, int(tp) + 1)
    image_file = d1[sf]
    l_file = d1['L numbers']
    proj_file = d1[of]
    image_file2 = d2[sf]
    l_file2 = d2['L numbers']
    proj_file2 = d2[of]

    mdisplay = matchdisplay.MatchDisplay(image_file, image_file2, proj_file, proj_file2)

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
    del(celldata2[1])
    mda = matchdata.MatchData(celldata1, celldata2)
    #ia1.onclick = overlay_highlighter(ov1, celldata1)

    #ia1.onclick = make_matcher(mda, ov2)

    #myhigh = overlay_highlighter(ov2, celldata2)

    #myhigh(568)

    #ov1.plot_points(celldata1[15], (255, 255, 255))

    ct = CompTracker(ov1, ov2, celldata1, celldata2, mda, midov)
    ia1.onclick = ct.set_left
    ia2.onclick = ct.set_right

    #start_ml = {
    #            432: 698,
    #            686: 1120,
    #            585: 974,
    #            739: 1186,
    #            548: 924,
    #            537: 913}

    #5 -> 6
    v = celldata.Coords2D((4, -38))
    # 6 -> 7
    #v = celldata.Coords2D((4, -13))
    # 7 -> 8
    #v = celldata.Coords2D((71, 42))
    mda.set_displacement(v)
    #mda.current_ml = start_ml
    #mda.update_displacement_array()
    mda.match_on_restricted_l(7, v)
    #mda.display_match(ov1, ov2, npa)

    mdisplay.display_array = npa
    mdisplay.mda = mda
    mdisplay.ovfrom = ov1
    mdisplay.ovto = ov2

    mda.lm = 0.95
    mda.um = 1.2
    mda.match_with_displacement_field(5)
    mda.lm = 0.90
    mda.um = 1.25
    mda.match_with_displacement_field(6)
    mda.lm = 0.85
    mda.um = 1.3
    mda.match_with_displacement_field(7)
    mda.lm = 0.78
    mda.um = 1.35
    mda.match_with_displacement_field(8)
    mda.match_with_displacement_field(9)
    mda.match_with_displacement_field(10)
    mda.match_with_displacement_field(10)
    print mda.get_average_v()
    #mdisplay.display_match(v)
    #mdisplay.display_match()

    #midov.save_to_png("mymatch.png")

    #delta_a = [float(cto.area) / float(cfrom.area) for cfrom, cto in mda.itermatches()]

    #print sum(delta_a) / len(delta_a)

    mda.get_divided_cells()
    mdisplay.display_match(v)
    #pprint.pprint(mda.divisions)

    #for cfrom, cto in mda.itermatches():
    #    ov1.plot_points(cfrom, (255, 255, 255))
    #    ov2.plot_points(cto, (255, 255, 255))
    #    

    #for fcid, tocids in mda.divisions.iteritems():
    ##    #print fcid, tocids
    #    print "%d -> %d, %d" % (fcid, tocids[0], tocids[1])
    #    print mda.cdfrom[fcid].color
    #    ov1.plot_points(mda.cdfrom[fcid], mda.cdfrom[fcid].color)
    #    ov2.plot_points(mda.cdto[tocids[0]], mda.cdfrom[fcid].color)
    #    ov2.plot_points(mda.cdto[tocids[1]], mda.cdfrom[fcid].color)

    while True:
        scale, (pan_x, pan_y) = input_loop(pygame.event.get(), scale, dmanager)
        px += pan_x
        py += pan_y
        dmanager.update()

if __name__ == '__main__':
    main()
