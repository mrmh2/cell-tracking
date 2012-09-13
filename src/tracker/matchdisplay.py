import sys
import pprint

import numpy as np
import pygame
from pygame.locals import *

import bb
import displaymanager as dm
import celldata
from celldata import Coords2D
import display
import intarray

def save_matchlist(ml):
    with open('matchlist.txt', 'w') as f:
        for k, v in ml.iteritems():
            f.write("%d: %s\n" % (k, v))

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

class CompTracker():
    def __init__(self, ov1, ov2, mda, midov, tleft):
        self.ov1 = ov1
        self.ov2 = ov2
        self.cd1 = mda.cdfrom
        self.cd2 = mda.cdto
        self.mda = mda
        self.midov = midov
        self.tleft = tleft

        self.leftcell = None
        self.rightcell = None

        self.center = Coords2D((352, 436))
        self.v = Coords2D((14, 37))

        self.mlex = {}

    def set_left(self, cid):
        self.leftcell = self.cd1[cid]
        self.leftcid = cid
        print "Set left to %d, area %d, centroid %s" % (cid, self.leftcell.area, self.leftcell.centroid)
        self.ov1.plot_points(self.cd1[cid], (255, 255, 255))
        v = Coords2D((4, -38))
        v = self.mda.get_displacement_a(self.leftcell.centroid)
        #self.ov2.plot_points(shiftit(border_list(self.cd1[cid]), v), (255, 255, 255))
        #self.midov.plot_points(self.cd1[cid], (255, 255, 255))
        print self.leftcell.lnumbers
        #best_m = self.mda.best_matches_on_l(cid, 10)
        self.tleft.add_text("Cell %d, centroid %s" % (cid, self.leftcell.centroid))

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
        #for cid, candidate in best_m:
        #    #candidate = self.mda.cdto[match_cid]
        #    d = adjusted_centroid.dist(candidate.centroid)
        #    if d < 10:
        #        self.ov2.plot_points(candidate, (255, 255, 255))

    def set_right(self, cid):
        self.rightcell = self.cd2[cid]
        self.rightcid = cid
        self.ov2.plot_points(self.cd2[cid], (255, 255, 255))
        print "Set right to %d, area %d, centroid %s" % (cid, self.rightcell.area, self.rightcell.centroid)
        print self.rightcell.lnumbers
        self.comp()

    def comp(self):
        if self.leftcell and self.rightcell:
            print "Left cell centroid:", self.leftcell.centroid
            print "Right cell centroid:", self.rightcell.centroid
            vdisp = self.center - self.leftcell.centroid
            print vdisp, abs(vdisp)
            vd = (self.rightcell.centroid - self.leftcell.centroid) - self.v
            print vd, abs(vd)

            print vdisp / -6
            
            pass

    def input_loop(self, events, scale, dmanager):
    
        px, py = 0, 0
    
        for event in events:
            if event.type == QUIT:
                sys.exit(0)
            elif event.type == KEYDOWN:
                print event.key
                if event.unicode == 'm':
                    print self.leftcid, ":", self.rightcid
                    self.mlex[self.leftcid] = [[self.rightcid]]
                if event.unicode == 's':
                    save_matchlist(self.mdisp.mda.current_ml)
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

def draw_single_vector(array, vfrom, vdisp):
    xf, yf = vfrom
    vx, vy = vdisp

    step = int(abs(vdisp))

    for i in range(0, step):
        r = i * 255
        g = 0
        b =  255 - (i * 255 / step)
        c = (r, g, b)
        px, py = xf + i * vx / step, yf + i * vy / step
        array[px, py] = c
        array[px-1, py] = c
        array[px+1, py] = c
        array[px, py-1] = c
        array[px, py+1] = c

class MatchDisplay():
    def __init__(
                    self, 
                    image_file,
                    image_file2,
                    proj_file,
                    proj_file2,
                    matchdata):

        self.mda = matchdata

        td = display.TrackerDisplay(0, 0, "Cell tracking")

        xdim, ydim = td.get_size()

        self.dmanager = dm.DisplayManager(td)
    
        bbox = bb.BoundingBox((0, 0), (xdim/3, ydim))
        bbox2 = bb.BoundingBox((2 * xdim/3, 0), (xdim/3, ydim))
        bbox3 = bb.BoundingBox((xdim/3, 0), (xdim/3, ydim))

        ov1, ia1 = self.create_image_with_overlay(bbox, image_file, proj_file)
        ov2, ia2 = self.create_image_with_overlay(bbox2, image_file2, proj_file2)

        npaxdim = max(ov1.xdim, ov2.xdim)
        npaydim = max(ov2.ydim, ov2.ydim)

        tbbox = bb.BoundingBox((0, 0), (300, 100))
        self.tleft = self.create_text_box(tbbox)
        self.tleft.add_text("Loaded %d cells" % len(self.mda.cdfrom))
        lx, ly, _ = ov1.array.shape
        self.tleft.add_text("Image is %dx%d" % (lx, ly))

        tbbox = bb.BoundingBox((2 * xdim/3, 0), (300, 100))
        self.tright = self.create_text_box(tbbox)
        self.tright.add_text("Loaded %d cells" % len(self.mda.cdto))
        rx, ry, _ = ov2.array.shape
        self.tright.add_text("Image is %dx%d" % (rx, ry))

        self.create_central_overlay(bbox3, npaxdim, npaydim)

        tbbox = bb.BoundingBox((xdim/3, 0), (300, 100))
        self.tmid = self.create_text_box(tbbox)
        self.tmid.add_text("Starting match...")

        self.ia1 = ia1
        self.ia2 = ia2

        #ct = CompTracker(ov1, ov2, self.mda, self.midov, self.tleft)
        #ia1.onclick = ct.set_left
        #ia2.onclick = ct.set_right
        #self.ct = ct
        #self.ct.mdisp = self

        self.ovfrom = ov1
        self.ovto = ov2

    def update(self):
        self.dmanager.update()

    def create_text_box(self, tbbox):
        da = dm.DisplayArea(tbbox)
        te = dm.TextBoxElement()
        da.add_element(te)
        self.dmanager.add_area(da)

        return te

    def create_central_overlay(self, bbox, xdim, ydim):
        da = dm.DisplayArea(bbox)
        npa = np.zeros([xdim, ydim, 3], dtype=np.int8)
        midov = dm.OverlayElement(npa, blank=True)
        da.add_element(midov)
        self.dmanager.add_area(da)
        self.midov = midov
 
    def create_image_with_overlay(self, bbox, ifile1, ifile2):
        da = dm.DisplayArea(bbox)
        de = dm.ImageElement(ifile1)
        #xdim1, ydim1 = de.xdim, de.ydim
        de2 = dm.ImageElement(ifile2, array=False)
        de2.visible = False
        de.iarray = intarray.InteractorArray(de.imgarray, de.shifts) 
        da.add_element(de)
        da.add_element(de2)
        ov = de.generate_overlay()
        da.add_element(ov)
        self.dmanager.add_area(da)

        return ov, de.iarray

    def display_match(self, vd=celldata.Coords2D((0, 0))):
        self.tmid.add_text("Updating, v=%s" % vd)
        self.update()
        array = self.midov.array
        for cellfrom, cellsto in self.mda.itermatches():
            #print cellfrom.centroid, cellsto[0].centroid
            vfrom = cellfrom.centroid
            self.ovfrom.plot_points(cellfrom, cellfrom.color)
            centroid_to = sum([cellto for cellto in cellsto], celldata.Cell([])).centroid
            vdisp = centroid_to - vfrom
            draw_single_vector(array, vfrom, vdisp - vd)
            for cellto in cellsto:
                self.ovto.plot_points(cellto, cellfrom.color)

        self.tmid.add_text("Found %d matches" % len(self.mda.current_ml))

#        lcx, lcy = self.mda.cdfrom.center
#        c = 255, 255, 255
#        self.ovfrom.array[lcx+0, lcy+0] = c
#        self.ovfrom.array[lcx+1, lcy+0] = c
#        self.ovfrom.array[lcx-1, lcy+0] = c
#        self.ovfrom.array[lcx+0, lcy+1] = c
#        self.ovfrom.array[lcx+0, lcy-1] = c
#
#        rcx, rcy = self.mda.cdto.center
#        c = 255, 255, 255
#        self.ovto.array[rcx+0, rcy+0] = c
#        self.ovto.array[rcx+1, rcy+0] = c
#        self.ovto.array[rcx-1, rcy+0] = c
#        self.ovto.array[rcx+0, rcy+1] = c
#        self.ovto.array[rcx+0, rcy-1] = c

        self.dmanager.update()
    
    def display_divisions(self):
        ov1 = self.ovfrom
        ov2 = self.ovto
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

    def run(self):
        scale = 1
        px, py = 0, 0
        while True:
            scale, (pan_x, pan_y) = self.ct.input_loop(pygame.event.get(), scale, self.dmanager)
            px += pan_x
            py += pan_y
            self.update()

    def display_single_match(self, cidfrom):
        cellfrom = self.mda.cdfrom[cidfrom]
        cidsto = self.mda.current_ml[cidfrom]
        cellsto = [self.mda.cdto[cidto] for cidto in cidsto]
        self.ovfrom.plot_points(cellfrom, cellfrom.color)
        for cellto in cellsto:
            self.ovto.plot_points(cellto, cellfrom.color)

    def highlight_cell(self, cell, c=(255, 255, 255)):
        if cell in self.mda.cdfrom.cells:
            self.ovfrom.plot_points(cell, c)
        if cell in self.mda.cdto.cells:
            self.ovto.plot_points(cell, c)

        
