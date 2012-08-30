#!/usr/bin/env python2.7

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

def overlay_highlighter(ov, cd):

    def highlight_it(cid):
        ov.plot_points(cd[cid], (255, 255, 255))

    return highlight_it

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
    image_file = 'data/newexp/rotated_image/T05.png'
    image_file2 = 'data/newexp/rotated_image/T06.png'
    proj_file = 'data/newexp/rotated_projection/T05.png'
    proj_file2 = 'data/newexp/rotated_projection/T06.png'
    
    #imgsurface = pygame.image.load(image_file)
    td = display.TrackerDisplay(xdim, ydim, caption_string)

    xdim, ydim = td.get_size()

    scale = 0.5
    px, py = 0, 0

    dmanager = dm.DisplayManager(td)

    bbox = bb.BoundingBox((0, 0), (xdim, ydim/2))
    bbox2 = bb.BoundingBox((0, ydim/2), (xdim, ydim/2))

    da = dm.DisplayArea(bbox)
    de = dm.ImageElement(image_file)
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
    de2 = dm.ImageElement(proj_file2, array=False)
    de2.visible = False
    ia2 = intarray.InteractorArray(de.imgarray) 
    de.iarray = ia2
    da.add_element(de)
    da.add_element(de2)
    ov2 = de.generate_overlay()
    da.add_element(ov2)
    dmanager.add_area(da)

    dmanager.update()

    celldata1 = celldata.CellData(image_file)
    ia1.onclick = overlay_highlighter(ov1, celldata1)

    ov1.plot_points(celldata1[15], (255, 255, 255))

    while True:
        scale, (pan_x, pan_y) = input_loop(pygame.event.get(), scale, dmanager)
        px += pan_x
        py += pan_y
        dmanager.update()
        #dm.draw(screen)

if __name__ == '__main__':
    main()
