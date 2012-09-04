#!/usr/bin/env python2.7

import sys

import pygame
import pygame.surfarray as surfarray
from pygame.locals import *

import bb

class TrackerDisplay():
    """TrackerDisplay is the display interface closest to the library graphics implementation.
    It should provide the ability to display images.
    """

    def __init__(self, xdim, ydim, caption):
        pygame.init()
        vinfo = pygame.display.Info()
        xdim = int(vinfo.current_w * 0.9)
        ydim = int(vinfo.current_h * 0.9)
        self.window = pygame.display.set_mode((xdim, ydim))
        pygame.display.set_caption(caption)
        self.screen = pygame.display.get_surface()
        self.xdim = xdim
        self.ydim = ydim

    def display_image(self, imgsurface, bbox, rescale=False):
        if rescale:
            tempsurface = pygame.transform.scale(imgsurface, (bbox.xdim, bbox.ydim))
            self.screen.blit(tempsurface, (bbox.x, bbox.y))
        else:
            self.screen.blit(imgsurface, (bbox.x, bbox.y))

    #def display_array(self, array, bbox):
    #    #xdim, ydim = array.shape
    #    tempsurface = pygame.surfarray.make_surface(array)
    #    self.screen.blit(tempsurface, (bbox.x, bbox.y))
    
    def update(self):
        pygame.display.update()

    def get_size(self):
        return self.xdim, self.ydim
        
