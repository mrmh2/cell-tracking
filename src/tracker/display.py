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
        self.window = pygame.display.set_mode((xdim, ydim))
        pygame.display.set_caption(caption)
        self.screen = pygame.display.get_surface()

    def display_image(self, imgsurface, bbox):
        tempsurface = pygame.transform.scale(imgsurface, (bbox.xdim, bbox.ydim))
        self.screen.blit(tempsurface, (bbox.x, bbox.y))
    
    def update(self):
        pygame.display.update()
