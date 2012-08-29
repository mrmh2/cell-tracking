#!/usr/bin/env python

import pprint
import pickle
import sys
import random
import hashlib
from math import sqrt

import pygame
import pygame.surfarray as surfarray
from pygame.locals import *
from Lforleather import *
import numpy

import celldata as cd

caption_string = "Cell tracking"
gsx = 0.35

debug = True

class MatchData:
    def __init__(self, xdim, ydim, celldata1, celldata2, lfile1, lfile2):
        self.fcelldata = celldata1
        self.tcelldata = celldata2
        self.cd1 = celldata1.cd
        self.cd2 = celldata2.cd

        self.carray = numpy.zeros((xdim, ydim))
        for cid2 in self.cd2.keys():
            x, y = get_centroid(self.cd2[cid2])
            #print "Cell %d at %d,%d" % (cid2, x, y)
            self.carray[x, y] = cid2

        self.darray = numpy.zeros((xdim, ydim, 3))
        self.fcols = {}
        for cid in self.cd1:
            self.fcols[cid] = shades_of_jop()
        self.d = 0
        self.v = (0, 0)

        self.lfile1 = lfile1
        self.lfile2 = lfile2

        self.ml = []
    
        self.ready = False

        self.vfunc = self.local_vector

        self.xdim = xdim
        self.ydim = ydim

        self.remove_v = False

        print "MD initialised, %dx%d" % (self.xdim, self.ydim)

    def make_ready(self):
        #self.m = build_matrix(self.lfile1, self.lfile2, weight_contrib, cachedir='/mnt/tmp')
        self.m = build_matrix(self.lfile1, self.lfile2, weight_contrib, cachedir=None)
        self.ready = True

    def set_display_panels(self, from_panel, to_panel, match_panel, extra_panel):
        self.fcelldata.set_disp_panel(from_panel) 
        self.tcelldata.set_disp_panel(to_panel) 
        self.disp_panel = match_panel
        self.extra_panel = extra_panel

    def dump_info(self):
        print sorted(self.cd1.keys())
        print sorted(self.cd2.keys())

    def update_dmatrix(self):
        for cid in self.ml:
            x1, y1 = get_centroid(self.cd1[cid])
            x2, y2 = get_centroid(self.cd2[self.ml[cid]])
            self.darray[x1, y1] = (x2 - x1, y2 - y1, 1)

    def iso_vector(self, p):
        ix, iy = calc_isotropic_growth_vector(p, (self.xdim/2, self.ydim/2), 0.025)
        vx, vy = self.v
        return vx + ix, vy + iy

    def get_vector(self, p):
        return self.vfunc(p)
  
    def local_vector(self, (x, y)):
        r = 50
        xs = self.darray[x-r:x+r,y-r:y+r, 0].sum()
        ys = self.darray[x-r:x+r,y-r:y+r, 1].sum()
        c = self.darray[x-r:x+r,y-r:y+r, 2].sum()

        #print xs, ys, c, xs /c, ys / c
        if c: return xs / c, ys / c
        else: return 0, 0

    def display(self):

        print self.ml

        print "Using offset vector", self.v
        cn = self.xdim / 2, self.ydim/2
        print "Offset at centre", cn, "is", self.local_vector((self.xdim/2, self.ydim/2))
    
        self.fcelldata.disp_panel.blank()
        self.tcelldata.disp_panel.blank()
        self.disp_panel.blank()

        for cid in self.ml:
            col = self.fcols[cid]
            self.fcelldata.highlight_cell(cid, col)
            cid2 = self.ml[cid]
            self.tcelldata.highlight_cell(cid2, col)
            #show_connection(self.cd1[cid], self.cd2[cid2], self.disp_panel.array, (v))
            if self.remove_v:
                show_connection(self.cd1[cid], self.cd2[cid2], self.disp_panel.array, self.v)
            else:
                show_connection(self.cd1[cid], self.cd2[cid2], self.disp_panel.array, (0, 0))

    def toggle_remove_v(self):
        if self.remove_v:
            self.remove_v = False
        else:
            self.remove_v = True

    def stage_1_match(self):
        self.ml = match_list_on_most_distinctive(self.m, 51)
        if(self.disp_panel): self.display()

    def stage_2_match(self):
        ds = [calc_2d_dist(get_centroid(self.cd1[cid]), get_centroid(self.cd2[self.ml[cid]])) for cid in self.ml]
        d = median(sorted(ds))
        self.ml = ml_filter_dist(self.ml, self.cd1, self.cd2, 0.9 * d)
        d, v = get_ml_stats(self.ml, self.cd1, self.cd2)
        self.d = d
        self.v = v
        if(self.disp_panel): self.display()

    def iterative_match(self):
        d, v = get_ml_stats(self.ml, self.cd1, self.cd2)
        self.ml = generate_a_bigger_match_list(self.cd1, self.cd2, self.m, self, v, 1.2 * d)
        self.d = d
        self.v = v
        if(self.disp_panel): self.display()
        #print get_ml_stats(s, f1.cd, f2.cd)

    def iso_match(self):
        d = 7
        self.vfunc = self.iso_vector
        #self.ml = match_list_with_localised_displacement(self.cd1, self.cd2, self.m, self, d)
        self.ml = vfunc_match(self, self.gen_iso_function(0.025))
        if(self.disp_panel): self.display()
        #print get_ml_stats(s, f1.cd, f2.cd)

    def match_with_localisation(self):
        d = 5
        self.update_dmatrix()
        self.vfunc = self.local_vector
        self.ml = match_list_with_localised_displacement(self.cd1, self.cd2, self.m, self, d)
        self.update_dmatrix()
        self.v = self.local_vector((self.xdim/2, self.ydim/2))
        #md = localisation(f1, f2, m, mln)
        #md.ml = mln
        if(self.disp_panel): self.display()

    def auto_match(self):
        self.stage_1_match()
        self.stage_2_match()
        self.iterative_match()
        self.match_with_localisation()

    def show_growth_heatmap(self):
        gs = []
        for cid in self.ml:
            cid2 = self.ml[cid]
            a1 = len(self.cd1[cid])
            a2 = len(self.cd2[self.ml[cid]])
            g = (float(a2) / float(a1)) - 1
            gs.append(g)
            c = int(300 * g)
            print "%d -> %d, %f" % (a1, a2, g)
            col = (127 + c, 127 - c, 0)
            self.tcelldata.highlight_cell(cid2, col)
            
        print min(gs), max(gs), median(gs)

    def show_stuff(self, cid):

        print "Displaying data for cell %d" % cid
        cparray = surfarray.array2d(self.limage)

        ox, oy = get_centroid(self.cd1[cid])
        ex, ey = 100, 100

        for x in range(-50,50):
            for y in range(-50, 50):
                try:
                    self.extra_panel.array[x + ex, y + ey] = cparray[x + ox, y + oy]
                except IndexError, e:
                    print "IndexError in show_stuff"

        pl = border_list(self.fcelldata.relative_rep(cid))

        self.extra_panel.draw_points_xy(pl, ex, ey, (255, 0, 0))

        self.extra_panel.array[ex, ey] = rgb_to_comp((255, 0, 0))
        self.extra_panel.array[ex+1, ey] = rgb_to_comp((255, 0, 0))
        self.extra_panel.array[ex-1, ey] = rgb_to_comp((255, 0, 0))
        self.extra_panel.array[ex, ey+1] = rgb_to_comp((255, 0, 0))
        self.extra_panel.array[ex, ey-1] = rgb_to_comp((255, 0, 0))

        vx, vy = self.get_vector((ox, oy))

        self.extra_panel.array[ex + vx, ey + vy] = rgb_to_comp((255, 0, 255))

        #self.extra_panel.draw_points_xy(pl, ex + vx, ey + vy, (0, 0, 255))

        self.extra_panel.draw_points_xy(pl, ex, ey, (255, 0, 0))

        #cid2 = find_a_match(self.cd1, self.cd2, self.m, self.md, self.v, 5, dpanel=self.extra_panel)

        print "** With get_vector:"
        cid2 = vectorised_match(self, cid, self.adj_get_vector(), disp=True)
        print "PIcked %d" % cid2
        print "** With iso_vector:"
        cid2 = vectorised_match(self, cid, self.gen_iso_function(0.025), disp=True)
        print "PIcked %d" % cid2

    def adj_get_vector(self):

        def getit((x, y)):
            vx, vy = self.v
            gx, gy = self.get_vector((x, y))
            return gx - vx, gy - vy

        return getit
        

    def gen_iso_function(self, k):
        def ifunc((x, y)):
            return calc_isotropic_growth_vector((x, y), (self.xdim/2, self.ydim/2), k)

        return ifunc

    def calc_isotropic_params(self):
        a = sorted(self.ml.keys())

        self.update_dmatrix()

        num = 0
        while num == 0:
            cids = random.sample(self.ml.keys(), 2)
            cid1 = cids[0]
            cid2 = cids[1]
            
            print "Chose %d, %d" % (cid1, cid2)
    
            p1 = get_centroid(self.cd1[cid1])
            p2 = get_centroid(self.cd1[cid2])
    
            v1 = self.local_vector(p1)
            v2 = self.local_vector(p2)
    
            p1x, p1y = p1
            p2x, p2y = p2
            v1x, v1y = v1
            v2x, v2y = v2
    
            print p1
            print p2
            print v1
            print v2

            num = p1x - p2x
    
        k = (v1x - v2x) / (p1x - p2x) 
        cx = p1x - (v1x / k)
        cy = p1y - (v1y / k)
        print "(%d, %d), %f)" % (cx, cy, k)

        self.isocen = (cx, cy)
        self.isok = k

        return self.isocen, self.isok

    def draw_vector_field(vfunc):

        pass

    def draw_interesting_things(self):

        self.disp_panel.blank()

        center = self.xdim / 2, self.ydim / 2
        k = 0.025
        for cid in self.ml:
            col = self.fcols[cid]
            self.fcelldata.highlight_cell(cid, col)
            cid2 = self.ml[cid]
            self.tcelldata.highlight_cell(cid2, col)
            #show_connection(self.cd1[cid], self.cd2[cid2], self.disp_panel.array, (v))
            #show_connection(self.cd1[cid], self.cd2[cid2], self.disp_panel.array, self.v)
            vx, vy = self.v

            x, y = get_centroid(self.cd1[cid])
            ix, iy = calc_isotropic_growth_vector((x, y), center, k)
            p2 = get_centroid(self.cd2[cid2])
            aline(self.disp_panel.array, (x + vx + ix, y + vy + iy), p2)




#        center = self.xdim / 2, self.ydim / 2
#        k = 0.02
#        for x in range(0, self.disp_panel.xdim, 20):
#            for y in range(0, self.disp_panel.ydim, 20):
#                p1 = x, y
#                vx, vy = calc_isotropic_growth_vector(p1, center, k)
#                p2 = x + vx, y + vy
#                aline(self.disp_panel.array, p1, p2)
#        pass

    def isotropic_growth(self, center, k):
        
        #self.disp_panel.blank()
        #for x in range(0, self.disp_panel.xdim, 20):
        #    for y in range(0, self.disp_panel.ydim, 20):
        #        p1 = x, y
        #        vx, vy = self.get_vector((x, y))
        #        p2 = x + vx, y + vy
#
#                aline(self.disp_panel.array, p1, p2)

        self.disp_panel.blank()

        cx, cy = center
        # TODO - make this nice
        for x in range(0, self.disp_panel.xdim, 20):
            for y in range(0, self.disp_panel.ydim, 20):
                p1 = x, y
                vx, vy = calc_isotropic_growth_vector(p1, center, k)
                p2 = x + vx, y + vy
                #p2 = x + k * (x - cx), y + k * (y - cy)
                aline(self.disp_panel.array, p1, p2)

    def show_best_matches(self, cid):

        try:
            cid2s = best_matches(self.m[cid], 10)
        except KeyError:
            cid2s = []

        pl =  self.fcelldata.relative_rep(cid)

        self.extra_panel.blank()
        self.extra_panel.draw_points_xy(pl, 250, 100, (255, 255, 255))

        self.fcelldata.disp_panel.blank()
        self.tcelldata.disp_panel.blank()

        l = 255
        oy = 200

        self.fcelldata.highlight_cell(cid, (255, 255, 255))

        for cid2 in cid2s:
            col = (l, l, l)
            self.tcelldata.highlight_cell(cid2, col)
            pl =  self.tcelldata.relative_rep(cid2)
            self.extra_panel.draw_points_xy(pl, 250, 100 + oy, (l, l, l))
            l -= 20
            oy += 50

    def save_to_file(self, filename):

        try:
            f = open(filename, "w")
        except IOError, e:
            print "Error opening %s for writing" % filename 
            print e
            return
        
        for cid in self.ml:
            x1, y1 = get_centroid(self.cd1[cid])
            x2, y2 = get_centroid(self.cd2[self.ml[cid]])
            f.write("%d,%d;%d,%d\n" % (x1 / gsx, y1 / gsx, x2 / gsx, y2 / gsx))

        f.close()

class Cell:
    points = {}

def calc_2d_dist(c1, c2):
    x1, y1 = c1
    x2, y2 = c2 
    return sqrt(pow(x2 - x1, 2) + pow(y2 - y1, 2))

def calc_isotropic_growth_vector(p, center, k):
    x, y = p
    cx, cy = center

    x1 = k * (x - cx)
    y1 = k * (y - cy)

    return x1, y1

def get_centroid(l):

    xsum = 0
    ysum = 0
    for x, y in l:
        xsum += x
        ysum += y

    return xsum / len(l), ysum / len(l)

def plot_cell(pl, array, xp, yp, color):

    for x, y in pl:
        array[x + xp, y + yp] = color

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

def test_plot(array, xp, yp, pl, c):

    cx, cy = get_centroid(pl)
    npl = [(x - cx, y - cy) for x, y in pl]
    plot_cell(npl, array, xp, yp, c)

def test_plot_border(array, xp, yp, pl, c):

    cx, cy = get_centroid(pl)
    npl = [(x - cx, y - cy) for x, y in pl]
    plot_cell(border_list(npl), array, xp, yp, c)

def calculate_scaling(fx1, fy1, fx2, fy2):
    return gsx, gsx

class IPanel():
    def __init__(self, filenames=None):
        if filenames is not None:
            self.surfaces = []
            for f in filenames:
                try:
                    self.surfaces.append(pygame.image.load(f))
                except pygame.error, e:
                    print "Failed to load %s" % f
                    print e
                    sys.exit(0)
            self.current_surface = self.surfaces[0]
            self.xdim, self.ydim = self.surfaces[0].get_size()
            self.i = 0
        
        sxdim = int(self.xdim * gsx)
        sydim = int(self.ydim * gsx)
        print "Original size of %s is (%d, %d), scaled size will be (%d, %d)" % (filenames[0], self.xdim, self.ydim, sxdim, sydim)
        ox, oy = self.surfaces[1].get_size()
        print "Size of alternative file is (%d, %d)" % (ox, oy)

    def cycle(self):
        self.i = 1 - self.i
        self.current_surface = self.surfaces[self.i]

    def scale(self, sx, sy):
        #print "Scale factor %fx%f" % (sx, sy)
        ns = []
        for s in self.surfaces:
            ns.append(pygame.transform.scale(s, (int(self.xdim * sx), int(self.ydim * sy))))
            #s = pygame.transform.scale(s, (int(self.xdim * sx), int(self.ydim * sy)))
        self.surfaces = ns
        self.xdim, self.ydim = self.surfaces[0].get_size()
        self.current_surface = self.surfaces[0]
        print "Scaled to %dx%d" % (self.xdim, self.ydim)

    def draw(self, surface, x, y):
        surface.blit(self.current_surface, (x, y))

class InputPanel: 
    def __init__(self, xdim, ydim):
        self.xdim = xdim
        self.ydim = ydim

    def mouse_input(self, x, y, button):
        #print "I am InputPanel's mouse_input at (%d, %d) button %d" % (x, y, button)
        cid = mangle_colour_value(self.array[x, y])
        if button == 1:
            self.b1handler(cid)
        elif button == 3:
            self.b2handler(cid)

class PVector:
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def __repr__(self):
        return "%s, %s" % (self.x, self.y)

    def __add__(self, other):
        return PVector(self.x + other.x, self.y + other.y)

class Panel():
    def draw(self, surface, x, y):
        surfarray.blit_array(self.surface, self.array)
        surface.blit(self.surface, (x, y))

    def __init__(self, xdim, ydim):
        self.xdim = xdim
        self.ydim = ydim
        self.surface = pygame.Surface([xdim, ydim])
        self.surface.set_colorkey((0, 0, 0))
        self.array = surfarray.array2d(self.surface)

    def draw_points(self, pl, col):
        c = rgb_to_comp(col)
        for x, y in pl:
            self.array[x, y] = c

    def draw_points_xy(self, pl, ox, oy, col):
        c = rgb_to_comp(col)

        for x, y in pl:
            self.array[x + ox, y + oy] = c

    def blank(self):
        self.array = self.array - self.array

class ScreenElement():
    def __init__(self, x, y, xdim, ydim, content):
        self.content = content
        self.x = x
        self.y = y
        self.position = PVector(x, y)
        self.bounding = PVector(xdim, ydim)
        self.xdim = xdim
        self.ydim = ydim

    def draw(self, surface):
        try:
            self.content.draw(surface, self.x, self.y)
        except AttributeError:
            pass

    def mouse_input(self, x, y, button):
        try:
            self.content.mouse_input(x, y, button)
        except AttributeError:
            pass

    def blank(self, surface):
        surface.fill((0, 0, 0))

def init_images(datapoints):
    ips = []

    for dp in datapoints:
        of = dp[0]
        sf = dp[1]
        ip = IPanel([of, sf])
        ip.scale(gsx, gsx)
        ips.append(ip)

    return ips

class MatchSet:
    def __init__(self, upper, lower, middle, ip_upper, ip_lower):
        self.upper = upper
        self.lower = lower
        self.middle = middle
        self.ip_upper = ip_upper
        self.ip_lower = ip_lower

def imgarray_from_file(filename, sx, sy):
    imgsurface = pygame.image.load(filename)
    xdim, ydim = imgsurface.get_size()
    imgsurface = pygame.transform.scale(imgsurface, (int(xdim * sx), int(ydim * sy)))
    array = surfarray.array2d(imgsurface)

    return array

def display_init(datapoints):

    ips = init_images(datapoints)

    gxdim = max([ip.xdim for ip in ips])
    gydim = max([ip.ydim for ip in ips])

    ps = []
    for i in range(0, 3):
        ps.append(Panel(gxdim, gydim))

    psize = 500
    ps.append(Panel(psize, 3 * gydim))

    imgarrays = []
    for dp in datapoints:
        sf = dp[1]
        ia = imgarray_from_file(sf, gsx, gsx)
        imgarrays.append(ia)

    se1 = ScreenElement(0, 0, gxdim, gydim, ips[0])
    se2 = ScreenElement(0, gydim, gxdim, gydim, ps[1])
    se3 = ScreenElement(0, 2 * gydim, gxdim, gydim, ips[1])
    se4 = ScreenElement(0, 0, gxdim, gydim, ps[0])
    se5 = ScreenElement(0, 2 * gydim, gxdim, gydim, ps[2])
    se6 = ScreenElement(0, 0, gxdim, gydim, InputPanel(gxdim, gydim))
    se7 = ScreenElement(0, 2 * gydim, gxdim, gydim, InputPanel(gxdim, gydim))
    se8 = ScreenElement(gxdim, 0, psize, 3 * gydim, ps[3])

    elements = [se1, se2, se3, se4, se5, se6, se7, se8]

    dm = DisplayManager(elements, ips)

    dm.imgarrays = imgarrays

    dm.upper = ps[0]
    dm.middle = ps[1]
    dm.lower = ps[2]
    dm.extra = ps[3]

    return dm


def init_screen(xdim, ydim):
    pygame.init()
    window = pygame.display.set_mode((xdim, ydim))
    pygame.display.set_caption(caption_string)
    screen = pygame.display.get_surface()

    return screen

def init(datapoints, i):
    global rpanel, myra
    frames = []
    pygame.init()

    #for dp in datapoints:
    #    f = Frame(dp[1], 0, 0)
    #    print "Image: %dx%d" % (f.xdim, f.ydim)
    #    f.secondary_surface(dp[0])
    #    f.scale_and_init(gsx, gsx)

    frame1_file = datapoints[i][1]
    frame1_orig = datapoints[i][0]

    frame2_file = datapoints[i + 1][1]
    frame2_orig = datapoints[i + 1][0]
    
    print "Loading images and making calculations"
    frame1 = Frame(frame1_file, 0, 0)
    frame2 = Frame(frame2_file, 0, 0)
    print "Image %d: %dx%d" % (1, frame1.xdim, frame1.ydim)
    print "Image %d: %dx%d" % (2, frame2.xdim, frame2.ydim)
    frame1.secondary_surface(frame1_orig)
    frame2.secondary_surface(frame2_orig)
    sx, sy = calculate_scaling(frame1.xdim, frame1.ydim, frame2.xdim, frame2.ydim)
    frame1.scale_and_init(sx, sy)
    frame2.scale_and_init(sx, sy)
    frame2.y = frame1.ydim
       
    bpx = max(frame1.xdim, frame2.xdim)
    bpanel = Panel(0, frame1.ydim + frame2.ydim, bpx, frame2.ydim)

    print "Initialising screen...",
    window = pygame.display.set_mode((frame1.xdim + psize, frame1.ydim + frame2.ydim + bpanel.ydim))
    pygame.display.set_caption(caption_string)
    screen = pygame.display.get_surface()
    print "done"

    frame1.flip_surface()
    frame2.flip_surface()


    #frame1.draw(screen)
    #frame2.draw(screen)

    rpanel = pygame.Surface([psize, frame1.ydim])
    rpanel.set_colorkey((0, 0, 0))
    myra = surfarray.array2d(rpanel)

    return screen, frame1, frame2, bpanel

def shades_of_jop():
    c1 = random.randint(127, 255) 
    c2 = random.randint(0, 127) 
    c3 = random.randint(0, 255) 

    #l = [c1, c2, c3]

    return tuple(random.sample([c1, c2, c3], 3))

def compositeRGB_to_components(c):
    R = c % 256
    G = int(c / 256) % 256
    B = int(c / (256 * 256)) % 256

    return (R, G, B)

def mangle_colour_value(c):
    r, g, b = compositeRGB_to_components(c)
    return b + 256 * g + 256 * 256 * r

def show_cell_thingies(frame1, frame2, m, cid):
    frame1.blank_overlay()
    frame1.highlight_cell(cid, (155, 155, 155))
    frame2.blank_overlay()
    col = (255, 255, 255)
    try:
        for ms in best_matches(m[cid], 10):
            frame2.highlight_cell(ms, col)
            #col -= 20
    except KeyError, e:
        print "Cell ID %d not in dictionary of L numbers" % cid

def draw_cell_on_panel(panel, x, y, pl, col):
    ox, oy = get_centroid(pl)

    for xp, yp in pl:
        panel.array[xp - ox + x, yp - oy + y] = col

def draw_cell_on_panel_nc(panel, pl, col):

    for xp, yp in pl:
        panel.array[xp, yp] = col

def best_guess(m, cid):
    try:
        return best_matches(m[cid], 1)[0]
    except KeyError, e:
        return -1

def nbest_guess(m, cid, n):
    try:
        return best_matches(m[cid], n)
    except KeyError, e:
        return -1

def rgb_to_comp(col):
    r, g, b = col
    return b + 256 * g + 256 * 256 * r 

def match_on_l_only(f1, f2, m, cid, v, md):
    vx, vy = v
    cid2s = nbest_guess(m, cid, 20)
    if cid2s != -1: 
        for cid2 in cid2s:
            x1, y1 = get_centroid(f1.cd[cid])
            p2 = get_centroid(f2.cd[cid2])

            d = calc_2d_dist((x1 + vx, y1 + vy), p2)
    
            if d < md:
                return cid2
    else:
        return -1

    return -1
    

def dprint(string):
    if debug:
        print string

def vectorised_match(md, cid, vfunc, disp=False):
    x, y = get_centroid(md.cd1[cid])
    print "Match from ", x, y
    ix, iy = vfunc((x, y))
    vx, vy = md.v
    #print ix + vx, iy + vy
    if disp:
        pl = border_list(md.fcelldata.relative_rep(cid))
        md.extra_panel.draw_points_xy(pl, 100 + vx + ix, 100 + vy + iy, (0, 0, 255))
    tx = x + ix + vx
    ty = y + iy + vy

    cid2s = nbest_guess(md.m, cid, 25)
    if cid2s != -1:
        for cid2 in cid2s:
            p2 = get_centroid(md.cd2[cid2])

            d = calc_2d_dist((x + tx, y + ty), p2)

            if d < 15:
                return cid2
    else:
        return -1

    a1 = len(md.cd1[cid])
    for oy in range(-10, 10):
        for ox in range(-10, 10):
            try:
                cid2c = md.carray[tx + ox, ty + oy]
                if cid2c != 0:
                    d = sqrt(ox * ox + oy * oy)
                    print "Try %d, dist %d" % (cid2c, d)
                    a2 = len(md.cd2[cid2c])
                    print "Areas %d, %d" % (a1, a2)
                    if d < 6:
                        print "dmatch, area difference %f" % (float(a2) / float(a1))
                        if a2 > 0.8 * a1 and a2 < 1.30 * a1:
                            return cid2c
            except IndexError, e:
                print "Out of range, %s", e

    return -1
 
def find_a_match(cd1, cd2, m, md, cid, v, max_d, verbose=False, dpanel=None):
    # First try L coefficient matching, with limited distances
    dprint("Attempting to find match for %d" % cid)

    cid2s = nbest_guess(m, cid, 25)
    if cid2s != -1: 
        for cid2 in cid2s:
            cx, cy = get_centroid(cd1[cid])
            vx, vy = v
            cx += vx
            cy += vy
            p2 = get_centroid(cd2[cid2])

            d = calc_2d_dist((cx, cy), p2)
    
            if d < (2 *max_d):
                return cid2
    else:
        return -1
    # Ok, we didn't find a match. Let's try nearest centroid. But be sane about areas
    
    cx, cy = get_centroid(cd1[cid])
    vx, vy = v
    cx += vx
    cy += vy

    a1 = len(cd1[cid])

    # URG
    #for ox, oy in range
    for oy in range(-10, 10):
        for ox in range(-10, 10):
  #          'print md.carray[cx + ox, cy + oy],
            try:
                cid2c = md.carray[cx + ox, cy + oy]
            except IndexError, e:
                print "Out of range, %s", e
                cid2c = 0
            if cid2c != 0 and sqrt(ox * ox + oy * oy) < (max_d / 2):
                print "Candidate match through centroids: %d" % cid2c
                a2 = len(cd2[cid2c])
                print "Areas %d, %d" % (a1, a2)
                if a2 > 0.80 * a1 and a2 < 1.25 * a1:
                    return md.carray[cx + ox, cy + oy]
                else:
                    print "Areas fail (%f). Bad centroids." % float(float(a1) / float(a2))
    
    return -1

def show_connection(cell1, cell2, disp_array, v):

    #print "Showing connection between %d and %d" % (cid1, cid2)
    #print "Areas are %d, %d" % (len(f1.cd[cid1]), len(f2.cd[cid2]))

    vx, vy = v

    x, y = get_centroid(cell1)
    p2 = get_centroid(cell2)
    aline(disp_array, (x + vx, y + vy), p2)

def display_match_data(md, from_panel, to_panel, display_panel, v):

    ml = md.ml
    
    print ml

    #f1.blank_overlay()
    #f2.blank_overlay()
    #pan.array = pan.array - pan.array
    display_panel.array = display_panel.array - display_panel.array
    for cid in ml:
        #print "Matched %d -> %d" % (cid, ml[cid])
        #f1.highlight_cell(cid, (255, 255, 255))
        #f1.highlight_cell(cid, shades_of_jop())
        #col = shades_of_jop()
        col = md.fcols[cid]
        md.fcelldata.highlight_cell(cid, col)
        #print "col", col
        #f1.highlight_cell(cid, col)
        #f2.highlight_cell(ml[cid], (255, 255, 255))
        #f2.highlight_cell(ml[cid], col)
        #show_connection(f1, f2, cid, ml[cid], pan, v)

def get_average_vector(cd1, cd2, ml):
    avx = 0
    avy = 0
    for cid in ml:
        cid2 = ml[cid]
        x1, y1 = get_centroid(cd1[cid])
        x2, y2 = get_centroid(cd2[cid2])
        avx += x2 - x1
        avy += y2 - y1

    return avx / len(ml), avy / len(ml)


def get_ml_stats(ml, cd1, cd2):
    ds = [calc_2d_dist(get_centroid(cd1[cid]), get_centroid(cd2[ml[cid]])) for cid in ml]
    d = median(sorted(ds))
    v = get_average_vector(cd1, cd2, ml)

    return d, v

def iterative_match(f1, f2, m, bpanel, md):
    ml = md.ml
    d, v = get_ml_stats(ml, f1.cd, f2.cd)
    mln = generate_a_bigger_match_list(f1, f2, m, v, 1.2 * d)
    md.d = d
    md.v = v
    md.ml = mln
    display_match_data(f1, f2, md, bpanel, v)
    print get_ml_stats(mln, f1.cd, f2.cd)
    return md

def match_with_localisation(f1, f2, m, md, bpanel):
    d = 5
    md.update_dmatrix(f1, f2)
    mln = match_list_with_localised_displacement(f1, f2, m, md, d)
    #md = localisation(f1, f2, m, mln)
    md.ml = mln
    display_match_data(f1, f2, md, bpanel, md.v)

    return md

def cheating_match(f1, f2, m, bpanel, ml):
    v = (10, -3)
    d = 10
    ml = generate_a_bigger_match_list(f1, f2, m, v, d)
    md = localisation(f1, f2, m, ml)
    md.ml = ml
    display_match_list(f1, f2, md, bpanel, v)
    return md

#def localisation(f1, f2, m, ml):
#    print "Generating displacement matrix...",
#    md = MatchData(f1.xdim, f1.ydim)
#    for cid in ml:
#        x1, y1 = get_centroid(f1.cd[cid])
#        x2, y2 = get_centroid(f2.cd[ml[cid]])
#        #print "(%d, %d)" % (x2 - x1, y2 - y1)
#        #print "b", md.darray[x1, y1]
#        md.darray[x1, y1] = (x2 - x1, y2 - y1, 1)
#        #print "a", md.darray[x1, y1]
#    #it = numpy.nditer(md.darray)
#    #for a in it:
#    #    print a
#    print "done"
#
#    print md.get_vector((500, 100))

#    ds = []
#    for cid in ml:
#        x1, y1 = get_centroid(f1.cd[cid])
#        x2, y2 = get_centroid(f2.cd[ml[cid]])
#        ox, oy = md.get_vector((x1, y1))
#        ds.append(calc_2d_dist((x1 + ox, y1 + oy), (x2, y2)))
#
#    print median(sorted(ds))
        
    return md

def make_pretty_stuff(ml, md, bpanel):
    bpanel.array = bpanel.array - bpanel.array
    for x in range(0, 1000, 20):
        for y in range(0, 300, 20):
            vx, vy = md.get_vector((x, y))
            p1 = x, y
            p2 = x + vx, y + vy
            aline(bpanel.array, p1, p2)
    

#def stage_3_match(f1, f2, m, bpanel, ml, d):
#    ml = generate_a_match_list(f1, f2, m, (0, 0), 1.5 * d)
#    display_match_data(f1, f2, md, bpanel, (0, 0))

#def do_n_cells(f1, f2, m, pan):
#    ml = generate_a_match_list(f1, f2, m, (0, 0))
#    #print ml
#    display_match_list(f1, f2, ml, pan, (0, 0))
#    furble_match_list(f1.cd, f2.cd, ml)

#def do_n_again(f1, f2, m, pan):
#    ml = generate_a_bigger_match_list(f1, f2, m, (9, -2))
#    #print ml
#    display_match_list(f1, f2, ml, pan, (0, 0))
#    furble_match_list(f1.cd, f2.cd, ml)

def generate_a_bigger_match_list(cd1, cd2, m, md, v, d):
    count = 0
    success = 0
    misses = 0

    ml = {}
    for cid in cd1.keys():
        print "Processing %d" % count
        count += 1
        #cid2 = match_on_l_only(f1, f2, m, cid, v)
        cid2 = find_a_match(cd1, cd2, m, md, cid, v, d)
        if cid2 != -1:
            ml[cid] = cid2
            success += 1
        else:
            misses += 1
           
    print "Successfully identified %d, %d misses" % (success, misses)

    return ml

def match_list_with_localised_displacement(cd1, cd2, m, md, d):
    count = 0
    misses = 0
    success = 0
    ml = {}

    for cid in cd1.keys():
        print "Processing %d" % count
        count +=1
        cx, cy = get_centroid(cd1[cid])
        v = md.get_vector((cx, cy))
        cid2 = find_a_match(cd1, cd2, m, md, cid, v, d)
        if cid2 != -1:
            ml[cid] = cid2
            success += 1
        else:
            misses += 1
           
    print "Successfully identified %d, %d misses" % (success, misses)

    return ml

def vfunc_match(md, vfunc):

    ml = {}

    for cid in md.cd1.keys():
        cid2 = vectorised_match(md, cid, vfunc)

        if cid2 != -1:
            ml[cid] = cid2

    return ml

def generate_a_match_list(f1, f2, m, v, d):
    count = 0
    success = 0
    misses = 0

    ml = {}
    for cid in f1.cd.keys():
        print "Processing %d" % count
        count += 1
        cid2 = match_on_l_only(f1, f2, m, cid, v, d)
        #cid2 = find_a_match(f1, f2, m, cid)
        if cid2 != -1:
            ml[cid] = cid2
            success += 1
        else:
            misses += 1
           
    print "Successfully identified %d, %d misses" % (success, misses)

    return ml

def aline(array, p1, p2):

    x1, y1 = p1
    x2, y2 = p2
    d = calc_2d_dist(p1, p2)

    step = int(d)

    #print "From (%d, %d) to (%d, %d), dist %d" % (x1, y1, x2, y2, d)
    
    v = x2 - x1, y2 - y1
    vx, vy = v
    for i in range(0, step):
        r = i * 255 / step
        b = 255 - (i * 255 / step)
        try:
            array[x1 + i * vx / step, y1 + i * vy / step] = rgb_to_comp((r, 0, b))
        except IndexError:
            pass

    #print v
 
def centroidy_stuff(f1, f2, m, cid, pan):

    p1 = get_centroid(f1.cd[cid])
    #pan.array[x1, y1] = r
   
    #pygame.draw.line(pan.surface, (255, 255, 255), (x1, y1), (x2, y2)) 

def get_unique_cids(filename):
    with open(filename, "r") as f:
        cids = [int(x.split(":")[0]) for x in f.readlines()]

    #print cids
    return cids

def filter_cells(frame, cidlist):
    for cid in frame.cd.keys():
        if cid not in cidlist and cid != 0:
            frame.highlight_cell(cid, (1, 1, 1))

class DisplayManager:
    def __init__(self, elements, ips):
        self.elements = elements
        self.ips = ips
        self.i1 = 0
        self.i2 = 1
        self.cmd = 0
        self.mode_string = "Loaded images"

    def set_surface(self, surface):
        self.surface = surface

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

def newinput(events, dm, md):

    for event in events:
        if event.type == QUIT:
            sys.exit(0)
        elif event.type == KEYDOWN:
            print event.key
            if event.key == 281:
                dm.page_down()
            elif event.key == 280:
                dm.page_up()
            elif event.key == 27:
                # ESC
                sys.exit(0)
            elif event.key == 293:
                print "Saving screenshot"
                pygame.image.save(dm.surface, "screenshot.png")
            elif event.key == 273:
                vx, vy = md.v
                md.v = vx, vy + 1
                md.display()
                # UP
            elif event.key == 274:
                vx, vy = md.v
                md.v = vx, vy - 1
                md.display()
                # DOWN
            elif event.key == 276:
                vx, vy = md.v
                md.v = vx - 1, vy
                md.display()
                # LEFT
            elif event.key == 275:
                vx, vy = md.v
                md.v = vx + 1, vy
                md.display()
                # RIGHT
            elif event.unicode == '`':
                dm.flip_surfaces()
            elif event.unicode == '1':
                #md = stage_1_match(frame1, frame2, m, bpanel, md)
                #md = stage_1_match(md)
                md.stage_1_match()
            elif event.unicode == '2':
                md.stage_2_match()
            elif event.unicode == '?':
                md.dump_info()
            elif event.unicode == 'i':
                md.iterative_match()
                #md.iso_match()
            elif event.unicode == 'o':
                md.iso_match()
            elif event.unicode == 'p':
                md.match_with_localisation()
            elif event.unicode == 's':
                md.save_to_file("matchout.txt")
            elif event.unicode == 'a':
                dm.draw_text("Searching infinite space")
                md.auto_match()
                dm.draw_text("Contemplating wonders of universe")
            elif event.unicode == 'h':
                md.show_growth_heatmap()

            elif event.unicode == 'g':
                md.isotropic_growth((-6147, 517), 0.00284)
            elif event.unicode == 'd':
                md.draw_interesting_things()
            elif event.unicode == 'v':
                md.toggle_remove_v()
                md.display()
            elif event.unicode == 'c':
                icxs = []
                icys = []
                ks = []
                for i in range(0, 10):
                    print "Iterating, %d" % i
                    ic, k = md.calc_isotropic_params()
                    icx, icy = ic
                    icxs.append(icx)
                    icys.append(icy)
                    ks.append(k)
                print median(icxs), median(icys), median(ks)


        elif event.type == MOUSEBUTTONDOWN:
            #print event.button

            x, y = pygame.mouse.get_pos()
            #print x, y

            dm.mouse_input(x, y, event.button)

def input(events, frame1, frame2, m, bpanel, screen, ml, md, i, elements):
    global d, gv
    
    for event in events:
        if event.type == QUIT:
            sys.exit(0)
        elif event.type == KEYDOWN:
            print event.key
            # TODO - get keysyms from somewhere
            if event.key == 280:
                # Page Up
                i = max(i - 1, 0)
            if event.key == 281:
                # Page Down
                i = i + 1
            if event.key == 32:
                lets_talk_about_centroids(m, frame1, frame2, 21)
            elif event.unicode == '1':
                md = stage_1_match(frame1, frame2, m, bpanel, md)
            elif event.unicode == '2':
                md = stage_2_match(frame1, frame2, m, bpanel, md)
            elif event.unicode == '3':
                stage_3_match(frame1, frame2, m, bpanel, ml, d)
            elif event.unicode == 'i':
                md = iterative_match(frame1, frame2, m, bpanel, md)
            elif event.unicode == 'l':
                md = localisation(frame1, frame2, m, ml)
            elif event.unicode == 'c':
                md = cheating_match(frame1, frame2, m, bpanel, ml)
                #do_n_cells(frame1, frame2, m, bpanel)
            elif event.unicode == 'p':
                md = match_with_localisation(frame1, frame2, m, md, bpanel)
            elif event.unicode == 'v':
                make_pretty_stuff(ml, md, bpanel)
            elif event.unicode == 'q':
                sys.exit(0)
            elif event.unicode == '`':
                frame1.flip_surface()
                frame2.flip_surface()
            elif event.unicode == 'f':
                filter_cells(frame1, m)
                cidlist = get_unique_cids("frame2-lcs.txt")
                #print sorted(cidlist)
                #print sorted (frame2.cd.keys())
                #filter_cells(frame2, cidlist)
                
        elif event.type == MOUSEBUTTONDOWN:
            print event.button

            x, y = pygame.mouse.get_pos()

            if event.button == 1:
                if y < frame1.ydim:
                    cid = mangle_colour_value(frame1.array[x, y])
                    frame1.blank_overlay()
                    frame1.highlight_cell(cid, (255, 255, 255))
                    frame2.blank_overlay()
                    vx, vy = md.get_vector((x, y))
                    print "Cursor at %d, %d. Displacement vector %d, %d" % (x, y, vx, vy)
                    cid2 = find_a_match(frame1, frame2, m, cid, (vx, vy), 3, verbose=True)
                    if cid2 != -1:
                        frame2.highlight_cell(cid2, (255, 255, 255))
    
                    print "Cell %d, size %d" % (cid, len(frame1.cd[cid]))
                else:
                    cid = mangle_colour_value(frame2.array[x, y-frame1.ydim])
                    print "Cell %d, size %d" % (cid, len(frame2.cd[cid]))
            elif event.button == 3:
                print md.get_vector((x, y))
                #if y < frame1.ydim:
                #    a = mangle_colour_value(frame1.array[x, y])
                #    show_cell_thingies(frame1, frame2, m, a)

    return ml, md, i
 
def build_celldict(imgarray):
    # TODO - probably (definitely) smarter ways to do this

    xdim, ydim = imgarray.shape
    cd = {}
    # Color values are mangled for some reason. Rather than recalculate the mangled color 
    # value for every single pixel in the image, let's build a hash table (dictionary)
    # as we go along
    md = {}
    
    for x in range(0, xdim):
        for y in range (0, ydim):
            c = imgarray[x, y]

            if md.has_key(c):
                a = md[c]
            else:
                md[c] = mangle_colour_value(c)
                a = md[c]

            if not cd.has_key(a): cd[a] = [(x, y)]
            else: cd[a].append((x, y))

    return cd

def cell_dict_from_file(image_file, sx, sy):
    """Take a numpy array containing values that represent segmentation ID, and return a
    dictionary keyed by the ID containing a list of points in absolute coordinates which
    comprise that cell"""

    try:
        imgsurface = pygame.image.load(image_file)
    except pygame.error, e:
        print "Couldn't load %s" % filename
        print e
        sys.exit(2)

    xdim, ydim = imgsurface.get_size()
    imgsurface = pygame.transform.scale(imgsurface, (int(xdim * sx), int(ydim * sy)))
    imgarray = surfarray.array2d(imgsurface)

    cmap = {}
    cd = {}
    for x in range(0, xdim):
        for y in range(0, ydim):

            val = imgarray[x, y]
            if val in cmap:
                c = cmap[val]
            else:
                r, g, b, a = imgsurface.unmap_rgb(val)
                c = b + 255 * g + 255 * 255 * r
                cmap[val] = c

            if c not in cd: cd[c] = [(x, y)]
            else: cd[c].append((x, y))

    return cd

def old_cell_dict_from_file(filename, sx, sy):
    try:
        imgsurface = pygame.image.load(filename)
        xdim, ydim = imgsurface.get_size()
        imgsurface = pygame.transform.scale(imgsurface, (int(xdim * sx), int(ydim * sy)))
        imgarray = surfarray.array2d(imgsurface)
        cd = build_celldict(imgarray)
    except pygame.error, e:
        print "Couldn't load %s" % filename
        print e
        sys.exit(2)

    return cd

def save_celldict(cd, filename):
    try:
        with open(filename, 'wb') as f:
            pickle.dump(cd, f)
    except IOError, e:
        print "Failed to open %s for writing" % filename
        print e
        sys.exit(0)

def cell_dict_with_caching(filename, sx, sy, cachedir):

    pickhash = hashlib.sha256(filename).hexdigest() + '.p'
    pickname = os.path.join(cachedir, pickhash)

    cd = cell_dict_from_file(filename, sx, sy)

    try:
        f = open(pickname, 'rb')
        #with open(pickname, 'rb') as f:
        print "Reading cached file...",
        cd = pickle.load(f)
        print "done"
    except IOError, e:
        if str(e).find("No such file") != -1:
            cd = cell_dict_from_file(filename, sx, sy)
            save_celldict(cd, pickname)
        else:
            print "Reading cached file failed"
            print e
            sys.exit(0)
    return cd

class CellData:
    def __init__(self, filename, sx, sy, cachedir='/mnt/tmp'):
        self.cd = cd.cell_dict_from_file(filename, sx, sy)

    def set_disp_panel(self, disp_panel):
        self.disp_panel = disp_panel

    def highlight_cell(self, cid, col, array=None):
        if array is None:
            try: 
                array = self.disp_panel.array
            except AttributeError:
                print "ERROR: No array to display to in highlight_cell"
                sys.exit(2)
        c = rgb_to_comp(col)
        for x, y in self.cd[cid]:
            array[x, y] = c

    def relative_rep(self, cid):
        ox, oy = get_centroid(self.cd[cid])

        npl = []
        for x, y in self.cd[cid]:
            npl.append((x - ox, y - oy))

        return npl

    

def highlight_cell(array, pl, col):
    for x, y in pl:
        array[x, y] = col * 256 * 256 + col * 256 + col

def median(l):
    n = int(len(l) / 2)

    return l[n]

def dump_cell_dicts(filename, frame):
    with open(filename, "w") as f:
        for cid in sorted(frame.cd.keys()):
            f.write("%d\n" % cid)

def lets_talk_about_centroids(m, frame1, frame2, n):
    frame1.blank_overlay()
    frame2.blank_overlay()

    ds = []
    print "MD:", most_distinctive(m, n)
    for cid in most_distinctive(m, n):
        frame1.highlight_cell(cid, (255, 255, 255))
    for cid in most_distinctive(m, n):
        cid2 = best_matches(m[cid], 1)[0]
        print "%d -> %d" % (cid, cid2)
        #print get_centroid(frame1.cd[cid]), get_centroid(frame2.cd[cid2])
        try:
            x1, y1 = get_centroid(frame1.cd[cid])
            x2, y2 = get_centroid(frame2.cd[cid2])
            #print 2d_dist(x1, y1, x2, y2)
            d = calc_2d_dist(get_centroid(frame1.cd[cid]), get_centroid(frame2.cd[cid2]))
            ds.append(d)
            if d < 50:
                frame1.highlight_cell(cid, (255, 255, 255))
                frame2.highlight_cell(cid2, (255, 255, 255))
            else:
                frame1.highlight_cell(cid, (100, 100, 100))
                frame2.highlight_cell(cid2, (100, 100, 100))
        except KeyError, e:
            print "Couldn't find key", e

    ds.sort()
    print ds
    print median(ds)

def cell_dist(cl1, cl2):
    return calc_2d_dist(get_centroid(cl1), get_centroid(cl2))

def dist_filter(cl1, cl2, d):
    if cell_dist(cl1, cl2) > d:
        return False
    else:
        return True

def print_ml(ml):
     for match in ml:
        print "%d -> %d" % (match, ml[match])

def ml_filter_dist(ml, cd1, cd2, d):
    mlf = {}
    for match in ml:
        if cell_dist(cd1[match], cd2[ml[match]]) <= d:
            mlf[match] = ml[match]
    return mlf

def match_list_on_most_distinctive(m, n):
    fcids = most_distinctive(m, n)
    ml = {}
    for fcid in fcids:
        ml[fcid] = best_matches(m[fcid], 1)[0]

    return ml

def stage_1_match(md):
    ml = match_list_on_most_distinctive(md.m, 51)
    md.ml = ml
    #display_match_data(md, from_panel, to_panel, display_panel, (0, 0))
    md.display()
    return md

def stage_2_match(f1, f2, m, bpanel, md):
    ds = [calc_2d_dist(get_centroid(f1.cd[cid]), get_centroid(f2.cd[md.ml[cid]])) for cid in md.ml]
    d = median(sorted(ds))
    #print_ml(ml)
    #md = MatchD
    md.ml = ml_filter_dist(md.ml, f1.cd, f2.cd, 0.9 * d)
    d, v = get_ml_stats(md.ml, f1.cd, f2.cd)
    print d, v
    display_match_data(f1, f2, md, bpanel, v)
    return md

def comp_contrib(ln, la, lb):
    return pow(la - lb, 2)

def weight_contrib(ln, la, lb):
    return ln * pow(la - lb, 2)

def read_datafile(filename):
    print "Reading data file %s" % filename
    with open(filename, "r") as f:
        tfs = f.readlines()

    d = [l.strip().split(",") for l in tfs]

    return d


def fit_all_elements(elements):

    xmax = max([e.x + e.xdim for e in elements])
    ymax = max([e.y + e.ydim for e in elements])

    return xmax, ymax
    
def old_loader():
    if len(sys.argv) > 1:
        trackfile = sys.argv[1]
    else:
        trackfile = "trackdata.txt"

    print "Reading trackfile...",
    datapoints = read_datafile(trackfile)
    print "done"

    return datapoints


def new_loader(expname):
    sys.path.insert(0, '/Users/hartleym/local/python')
    import get_data_files as gdf

    #trackfile = 'src/tracker/trackdata.txt'
    #datapoints = read_datafile(trackfile)
    #print datapoints

    d = gdf.get_data_files(expname)
    dps = []
    for dp in sorted(d.iteritems()):
        name, vd = dp
        a = [vd['Rotated projection'], vd['Rotated image'], vd['L numbers']]
        dps.append(a)

    return dps[:2]



def main():
    global myra, rpanel

    datapoints = new_loader(sys.argv[1])

    print "Initialising display manager...",
    dm = display_init(datapoints)
    print "Done"
    xdim, ydim = fit_all_elements(dm.elements)
    #cd1 = CellData(datapoints[0][1], gsx, gsx)
    #cd2 = CellData(datapoints[1][1], gsx, gsx)

    cds = []
    for dp in datapoints:
        print "Building cell dictionary...",  
        cd = CellData(dp[1], gsx, gsx)
        print "%d cells" % len(cd.cd)
        cds.append(cd)

    #sys.exit(0)
    mds = []
    for i in range(0, len(datapoints) - 1):
        lf1 = datapoints[i][2]
        lf2 = datapoints[i+1][2]
        md = MatchData(dm.elements[0].xdim, dm.elements[0].ydim, cds[i], cds[i+1], lf1, lf2)
        mds.append(md)


    dm.mds = mds
    dm.set_current_md(0)

    screen = init_screen(xdim, ydim)
    dm.surface = screen

    while True:
        newinput(pygame.event.get(), dm, dm.current_md)
        pygame.display.update()
        dm.draw(screen)

if __name__ == "__main__":
    main()
