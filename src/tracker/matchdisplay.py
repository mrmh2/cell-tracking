import displaymanager as dm
import celldata

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
                    prof_file2):
        pass

    def display_match(self, vd=celldata.Coords2D((0, 0))):
        array = self.display_array

        for cellfrom, cellsto in self.mda.itermatches():
            vfrom = cellfrom.centroid
            self.ovfrom.plot_points(cellfrom, cellfrom.color)
            centroid_to = sum([cellto for cellto in cellsto], celldata.Cell([])).centroid
            vdisp = centroid_to - vfrom
            draw_single_vector(array, vfrom, vdisp - vd)
            for cellto in cellsto:
                self.ovto.plot_points(cellto, cellfrom.color)
