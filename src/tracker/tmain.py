#!/usr/bin/env python2.7

import sys

import pygame
import pygame.surfarray as surfarray
from pygame.locals import *

import bb
import display
import displaymanager as dm

def input_loop(events, scale):

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

    pan = (px, py)

    return scale, pan

def main():

    xdim = 1024
    ydim = 600
    caption_string = "Display test"
    image_file = 'data/newexp/rotated_image/T08.png'
    image_file2 = 'data/newexp/rotated_image/T09.png'
    proj_file = 'data/newexp/rotated_projection/T08.png'
    
    #imgsurface = pygame.image.load(image_file)
    td = display.TrackerDisplay(xdim, ydim, caption_string)

    scale = 0.5
    px, py = 0, 0

    dmanager = dm.DisplayManager(td)

    bbox = bb.BoundingBox((0, 0), (xdim, ydim/2))
    bbox2 = bb.BoundingBox((0, ydim/2), (xdim, ydim/2))

    da = dm.DisplayArea(bbox)
    de = dm.ImageElement(image_file)
    de2 = dm.ImageElement(proj_file)
    da.add_element(de)
    da.add_element(de2)
    dmanager.add_area(da)

    da = dm.DisplayArea(bbox2)
    de = dm.ImageElement(image_file2)
    da.add_element(de)
    dmanager.add_area(da)

    while True:
        scale, (pan_x, pan_y) = input_loop(pygame.event.get(), scale)
        px += pan_x
        py += pan_y
        dmanager.update()
        #dm.draw(screen)

if __name__ == '__main__':
    main()
