import sys

import scipy.misc
import numpy as np
import pygame

import intarray
import display
import bb

class DisplayElement(object):
    def __init__(self):
        pass

    def toggle_visible(self):
        self.visible = not self.visible

    def mouse_input(self, p, button):
        pass
        #print "Base method"

class TextBoxElement(DisplayElement):

    def __init__(self):
        self.font = pygame.font.Font(None, 20)
        self.tbuffer = ["Loading..."]
        self.xdim = 300
        self.ydim = 200
        self.surface = pygame.Surface((self.xdim, self.ydim))
        self.surface.set_colorkey((0, 0, 0))

    def draw(self, display, bbox):
        self.surface.fill(0)
        ypos = 0
        for text in reversed(self.tbuffer):
            c = 255 - 2 * ypos
            self.label = self.font.render(text, 1, (c, c, c))
            self.surface.blit(self.label, (0, ypos))
            ypos += 20

        display.display_image(self.surface, bbox, rescale=False)

    def add_text(self, text):
        self.tbuffer.append(text)
        if len(self.tbuffer) > 4:
            del(self.tbuffer[0])
 

class OverlayElement(DisplayElement):
    def __init__(self, array, blank=False):
        self.array = array
        self.surface = pygame.surfarray.make_surface(array)
        self.surface.set_colorkey((0, 0, 0))
        self.xdim, self.ydim = self.surface.get_size()
        self.visible = True
        self.shouldblank = blank
        self.rescale = True
        print "OverlayElement initialised with size", self.surface.get_size()

    def draw(self, display, bbox):

        s, dbox = get_scale_and_box(self.xdim, self.ydim, bbox)
        
        #if self.ydim > self.xdim:
        #    aspect_ratio = float(self.xdim) / float(self.ydim)
        #    dbox = bb.BoundingBox((bbox.x, bbox.y), (int(aspect_ratio * bbox.ydim), bbox.ydim))
        #else:
        #    aspect_ratio = float(self.ydim) / float(self.xdim)
        #    dbox = bb.BoundingBox((bbox.x, bbox.y), (bbox.xdim, int(aspect_ratio * bbox.xdim)))

        if self.visible:
            pygame.surfarray.blit_array(self.surface, self.array)
            display.display_image(self.surface, dbox, rescale=self.rescale, blank=self.shouldblank)

    def save_to_png(self, filename):
        scipy.misc.imsave(filename, self.array)

    def __setitem__(self, (x, y),  c):
        self.array[x, y] = c

    def blank(self):
    # TODO - this could be better (find type and set zeros)
        self.array = self.array - self.array

    def plot_points(self, pl, c):
        for p in pl:
            x, y = p
            #print "Plotting %d, %d" % (x, y)
            self[x, y] = c

def get_scale_and_box(xdim, ydim, bbox):
    sx = float(bbox.xdim) / float(xdim)
    sy = float(bbox.ydim) / float(ydim)

    s = min(sx, sy)

    nxdim = int(s * xdim)
    nydim = int(s * ydim)

    return s, bb.BoundingBox((bbox.x, bbox.y), (nxdim, nydim))

class ImageElement(DisplayElement):
    def __init__(self, filename, array=True, scale=(1,1)):
        sx, sy = scale
        self.imgsurface = pygame.image.load(filename)
        self.xdim, self.ydim = self.imgsurface.get_size()
        self.imgsurface = pygame.transform.scale(self.imgsurface, 
            (int(sx * self.xdim), int(sy * self.ydim)))
        self.xdim, self.ydim = self.imgsurface.get_size()
        self.visible = True
        if array:
            self.imgarray = pygame.surfarray.array2d(self.imgsurface)
        else:
            self.imgarray = None
        self.rescale = True

    def generate_overlay(self):
        xdim, ydim = self.xdim, self.ydim
        npa = np.zeros([xdim, ydim, 3], dtype=np.int8)
        return OverlayElement(npa)

    def draw(self, display, bbox):

        s, dbox = get_scale_and_box(self.xdim, self.ydim, bbox)

        if self.visible:
            display.display_image(self.imgsurface, dbox, rescale=self.rescale)
    
        self.cmult =  1 / s

    def mouse_input(self, p, button):
        x, y = p
        cx, cy =  int(x * self.cmult), int(y * self.cmult)

        try:
            iarray = self.iarray
        except AttributeError:
            iarray = None

        if iarray is not None:
            self.iarray.mouse_click((cx, cy), button)
        #    pass
        #if self.imgarray is not None:
            #self.array_handler(
            #print self.imgarray[cx, cy]

        #self.show_info()

    def show_info(self):
        print self.imgsurface.get_size()
        print self.imgarray.shape

    @property
    def shifts(self):
        return self.imgsurface.get_shifts()


class DisplayArea:
    def __init__(self, bbox):
        self.x = bbox.x
        self.y = bbox.y
        self.xdim = bbox.xdim
        self.ydim = bbox.ydim
        self.bbox = bbox
        self.delements = []

    def add_element(self, delement):
        self.delements.append(delement)

    def update(self, display):
        for de in self.delements:
            de.draw(display, self.bbox)

    def mouse_input(self, (x, y), button):
        for de in self.delements:
            de.mouse_input((x - self.x, y - self.y), button)
    

class DisplayManager():
    def __init__(self, tdisplay=None):
        self.tdisplay = tdisplay
        self.xdim, self.ydim = tdisplay.get_size()
        self.dareas = []
        #self.elements = elements
        #self.ips = ips
        #self.i1 = 0
        #self.i2 = 1
        #self.cmd = 0
        #self.mode_string = "Loaded images"

    def mouse_input(self, p, button):
        for a in self.dareas:
            if a.bbox.contains(p):
                a.mouse_input(p, button)
        
    def key_input(self, keyval):
        if keyval == 314:
            for a in self.dareas:
                for e in a.delements:
                    if isinstance(e, ImageElement):
                        e.toggle_visible()
        if keyval == 32:
            for a in self.dareas:
                for e in a.delements:
                    try:
                        e.rescale = not e.rescale
                    except AttributeError:
                        pass

    def update(self):
        for da in self.dareas:
            da.update(self.tdisplay)
        self.tdisplay.update()

    def add_area(self, darea):
        self.dareas.append(darea)


    ########################################################
    # OLD
    ########################################################

    def draw(self, surface=None):
        if surface == None:
            surface = self.surface
        surface.fill((0, 0, 0))
        for e in self.elements:
            e.draw(surface)
        self.draw_text(self.mode_string)

    def draw_text(self, message):
        font = pygame.font.Font(None, 36)
        text = font.render(message, 1, (255, 255, 255))
        #textpos = text.get_rect(centerx=surface.get_width()/2)
        self.surface.blit(text, (1200, 700))
        self.mode_string = message
        pygame.display.update()

    def flip_surfaces(self):
        self.elements[0].content.cycle()
        self.elements[2].content.cycle()

    def set_current_md(self, i):
        self.cmd = i
        self.current_md = self.mds[i]
        if not self.current_md.ready:
            self.current_md.make_ready()
        self.elements[0].content = self.ips[i]
        self.elements[2].content = self.ips[i+1]
        self.current_md.set_display_panels(self.upper, self.lower, self.middle, self.extra)
        self.current_md.display()
        self.elements[5].content.array = self.imgarrays[i]
        #self.elements[5].content.b1handler = self.current_md.fcelldata.highlight_cell
        #self.elements[5].content.b1handler = self.current_md.show_best_matches
        self.elements[5].content.b1handler = self.current_md.show_stuff
        self.elements[5].content.b2handler = self.current_md.show_best_matches
        self.elements[6].content.array = self.imgarrays[i + 1]
        self.elements[6].content.b1handler = self.current_md.tcelldata.highlight_cell
    
        self.current_md.uimage = self.elements[0].content.current_surface
        self.current_md.limage = self.elements[2].content.current_surface

    #def mouse_input(self, x, y, button):
    #    for e in self.elements:
    #        #print e.x, e.y, e.x + e.xdim, e.y + e.ydim
    #        if x > e.x and x < e.x + e.xdim and y > e.y and y < e.y + e.ydim:
    #            e.mouse_input(x - e.x, y - e.y, button)
    #            #print "Match"

    def page_up(self):

        if self.cmd > 0:
            self.cmd -= 1
            self.set_current_md(self.cmd)

    def page_down(self):
        if self.cmd + 1 < len(self.mds):
            self.cmd += 1
            self.set_current_md(self.cmd)


