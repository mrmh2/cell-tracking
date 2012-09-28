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
from mutil import msum

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
                    matchdata,
                    scale=(1,1)):

        self.mda = matchdata

        td = display.TrackerDisplay(0, 0, "Cell tracking")

        xdim, ydim = td.get_size()

        self.dmanager = dm.DisplayManager(td)
    
        bbox = bb.BoundingBox((0, 0), (xdim/3, ydim))
        bbox2 = bb.BoundingBox((2 * xdim/3, 0), (xdim/3, ydim))
        bbox3 = bb.BoundingBox((xdim/3, 0), (xdim/3, ydim))

        ov1, ia1 = self.create_image_with_overlay(bbox, image_file, proj_file)
        ov2, ia2 = self.create_image_with_overlay(bbox2, image_file2, proj_file2, scale=scale)

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

    def screenshot(self, filename):
        pygame.image.save(self.dmanager.tdisplay.screen, filename)

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
 
    def create_image_with_overlay(self, bbox, ifile1, ifile2, scale=(1,1)):
        da = dm.DisplayArea(bbox)
        de = dm.ImageElement(ifile1, scale=scale)
        #xdim1, ydim1 = de.xdim, de.ydim
        de2 = dm.ImageElement(ifile2, scale=scale, array=False)
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
        self.ovfrom.blank()
        self.ovto.blank()
        self.midov.blank()
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

        self.update()
    
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

    def plot_some_shit(self, vd):
        self.mda.update_iso_params()
        self.midov.blank()

        #center = Coords2D((320, 470))
        #vd = Coords2D((56, 55))
        for cell, csto in self.mda.itermatches():
            pred_vdisp = self.mda.iso_vdisp(cell.centroid)
            #draw_single_vector(self.midov.array, cell.centroid, vdisp)
        #inp = [(f.centroid, msum([t for t in ts]).centroid )
            vdisp = msum([cto for cto in csto]).centroid - cell.centroid
            draw_single_vector(self.midov.array, cell.centroid, vdisp - pred_vdisp)

        self.update()
        
