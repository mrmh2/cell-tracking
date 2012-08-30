import pygame

import display
import bb

class DisplayElement():
    def __init__(self):
        pass

class ImageElement(DisplayElement):
    def __init__(self, filename):
        self.imgsurface = pygame.image.load(filename)
        self.xdim, self.ydim = self.imgsurface.get_size()

    def draw(self, display, bbox):
        aspect_ratio = float(self.xdim) / float(self.ydim)
        dbox = bb.BoundingBox((bbox.x, bbox.y), (int(aspect_ratio * bbox.ydim), bbox.ydim))
        display.display_image(self.imgsurface, dbox)

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
    

class DisplayManager():
    def __init__(self, tdisplay=None):
        self.tdisplay = tdisplay
        self.dareas = []
        #self.elements = elements
        #self.ips = ips
        #self.i1 = 0
        #self.i2 = 1
        #self.cmd = 0
        #self.mode_string = "Loaded images"

    def update(self):
        for da in self.dareas:
            da.update(self.tdisplay)
        self.tdisplay.update()

    def add_area(self, darea):
        self.dareas.append(darea)

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

    def mouse_input(self, x, y, button):
        for e in self.elements:
            #print e.x, e.y, e.x + e.xdim, e.y + e.ydim
            if x > e.x and x < e.x + e.xdim and y > e.y and y < e.y + e.ydim:
                e.mouse_input(x - e.x, y - e.y, button)
                #print "Match"

    def page_up(self):

        if self.cmd > 0:
            self.cmd -= 1
            self.set_current_md(self.cmd)

    def page_down(self):
        if self.cmd + 1 < len(self.mds):
            self.cmd += 1
            self.set_current_md(self.cmd)


