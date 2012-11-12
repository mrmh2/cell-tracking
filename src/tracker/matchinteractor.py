import sys

import pygame
from pygame.locals import *

from coords2d import Coords2D

class MatchInteractor():
    def __init__(self, mdisplay):
        self.ov1 = mdisplay.ovfrom
        self.ov2 = mdisplay.ovto
        self.cd1 = mdisplay.mda.cdfrom
        self.cd2 = mdisplay.mda.cdto
        self.mda = mdisplay.mda
        self.midov = mdisplay.midov
        self.tleft = mdisplay.tleft
        self.tright = mdisplay.tright

        self.mdisplay = mdisplay

        self.leftcell = None
        self.rightcells = []

        self.leftcid = None
        self.rightcid = None
        self.rightcids = []

        # TODO - interactor arrays should really belong to the match interactor
        mdisplay.ia1.onclick = self.set_left
        mdisplay.ia2.onclick = self.set_right

        self.center = Coords2D((352, 436))
        self.v = Coords2D((14, 37))

        self.mlex = {}

    def set_left(self, cid):
        if self.leftcid == cid:
            self.mdisplay.highlight_cell(self.leftcell, (0, 0, 0))
            self.leftcid = None
            self.leftcell = None
        else:
            try:
                self.leftcell = self.cd1[cid]
            except KeyError:
                self.leftcell = None
                return
            self.leftcid = cid
            print "Set left to %d, area %d, centroid %s" % (cid, self.leftcell.area, self.leftcell.centroid)
            self.tleft.add_text("Cell %d, area %d, centroid %s" % (cid, self.leftcell.area, self.leftcell.centroid))
            self.mdisplay.highlight_cell(self.leftcell)
        #self.ov1.plot_points(self.cd1[cid], (255, 255, 255))
        #v = Coords2D((4, -38))
        #v = self.mda.get_displacement_a(self.leftcell.centroid)
        #self.ov2.plot_points(shiftit(border_list(self.cd1[cid]), v), (255, 255, 255))
        #self.midov.plot_points(self.cd1[cid], (255, 255, 255))
            self.comp()

    def set_right(self, cid):
        try:
            cell = self.cd2[cid]
        except KeyError:
            return

        if cid in self.rightcids:
            self.mdisplay.highlight_cell(cell, (0, 0, 0))
            self.rightcids.remove(cid)
            self.rightcells.remove(cell)
        else:
            self.rightcids.append(cid)
            #cell = self.cd2[cid]
            self.rightcells.append(self.cd2[cid])
            print "Set right to %d, area %d, centroid %s" % (cid, cell.area, cell.centroid)
            self.tright.add_text("Cell %d, area %d, centroid %s" % (cid, cell.area, cell.centroid))
            self.mdisplay.highlight_cell(cell)
            self.comp()

    def comp(self):
        if self.leftcell and len(self.rightcells):
            #print "Left cell centroid:", self.leftcell.centroid
            #print "Right cell centroid:", self.rightcell.centroid
            vdisp = self.center - self.leftcell.centroid
            #print vdisp, abs(vdisp)
            #vd = (self.rightcell.centroid - self.leftcell.centroid) - self.v
            #print vd, abs(vd)

            #print vdisp / -6
            
    def input_loop(self, events, scale, dmanager):
    
        px, py = 0, 0
    
        for event in events:
            if event.type == QUIT:
                sys.exit(0)
            elif event.type == KEYDOWN:
                print event.key
                if event.unicode == 'm':
                    print self.leftcid, ":", self.rightcids
                    #self.mlex[self.leftcid] = [[self.rightcid]]
                    self.mdisplay.mda.current_ml[self.leftcid] = self.rightcids
                    self.mdisplay.display_single_match(self.leftcid)
                    self.leftcid = None
                    self.rightcids = []
                if event.unicode == ']':
                    self.mdisplay.plot_some_shit(self.mdisplay.mda.get_average_v())
                if event.unicode == ' ':
                    dmanager.key_input(32)
                if event.unicode == 'p':
                    self.mdisplay.mda.print_match_stats()
                if event.unicode == 's':
                    self.mdisplay.mda.save_matchlist('matchdata.txt')
                if event.unicode == 'u':
                    self.mdisplay.display_match(self.mdisplay.mda.get_average_v())
                if event.unicode == '1':
                    self.mdisplay.mda.lm = 0.60
                    self.mdisplay.mda.um = 1.1
                    self.mdisplay.mda.stage_1_hinted_match(5)
                    self.mdisplay.display_match(self.mdisplay.mda.get_average_v())
                if event.unicode == '2':
                    self.mdisplay.mda.stage_2_hinted_match(7)
                    self.mdisplay.display_match(self.mdisplay.mda.get_average_v())
                if event.unicode == '3':
                    self.mdisplay.mda.stage_3_hinted_match(7)
                    self.mdisplay.display_match(self.mdisplay.mda.get_average_v())
                if event.unicode == '4':
                    self.mdisplay.mda.stage_4_hinted_match(7)
                    self.mdisplay.display_match(self.mdisplay.mda.get_average_v())
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

    def run(self):
        scale = 1
        px, py = 0, 0
        while True:
            scale, (pan_x, pan_y) = self.input_loop(pygame.event.get(), scale, self.mdisplay.dmanager)
            px += pan_x
            py += pan_y
            self.mdisplay.update()
 
 
