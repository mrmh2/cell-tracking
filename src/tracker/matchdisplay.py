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
        ml = self.mda.current_ml

        # TODO - nicenise this interface
        for cidfrom, cidsto in ml.iteritems():
            cell_from = self.mda.cdfrom[cidfrom]
            centroid_from = cell_from.centroid()
            self.ovfrom.plot_points(cell_from, cell_from.color)

            for cidto in cidsto:
                cell_to = self.mda.cdto[cidto]
                centroid_to = cell_to.centroid()

                vfrom = centroid_from
                vdisp = centroid_to - centroid_from

                draw_single_vector(array, vfrom, vdisp - vd)

                self.ovto.plot_points(cell_to, cell_from.color)

